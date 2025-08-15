"""
This module loads data from Multi-aging study and loads it into a relational database
for simplified visualization and processing.
"""

from datetime import datetime, timedelta
from typing import Optional, Iterable

import numpy as np

from battery_health.multi_aging_exp.data_import import import_datafile, SensorDataNotFound
import battery_health.multi_aging_exp.feature_extraction as ext


def infer_stage(file):
    if "Stage_1" in str(file):
        return 1
    elif "Stage_2" in str(file):
        return 2
    else:
        raise ValueError("No stage in path!")


MEASUREMENT_CORRECTIONS = {
         # These are the ones that fail to parse via the datetime module.
         # There are other improperly input dates (easy to see when plotting calendar time),
         # but I will have to identify these by statistical methods.
         "29.02.2023": datetime(2023, 3, 1),
         "22.10.222.12.233": datetime(2023, 1, 19),
         "xx.12.2021": datetime(2021, 12, 5),
         "13.17.2023": datetime(2023, 7, 13)
}


class Measurement:
    def __init__(self, file):
        self.file = file
        self.infer_stage()
        self.parse_filename()
        self.experiment_id = "_".join([self.experiment, str(self.stage)])
        self.read_meta()
        self.read_sensor_file()

        # The date which the first Measurement of the experiment is run.
        # This is used as a starting point for the "calendar time." It must be
        # set externally since it depends on other measurements of the same experiment.
        self.experiment_start = None
        self._cum_fec = None

    @property
    def row(self):
        """
        Return a dictionary representing each row in the measurement table.
        
        Fields:
            experiment_id (str) -- ID of experiment to which measurement belongs
            number (int) -- Number of measurement in the experimental sequence
            type (str) -- each measurement is either some type of checkup (initial / extended / final / regular)
                or a cycling measurement
            calendar_time (float) -- Number of days from the start of the experiment until either the capacity measurement
                (for checkups) or the start of the measurement (for cycling).
            cum_fec (float) -- Number of full equivalent cycles prior to the start of the measurement
            fec (float) -- Number of full equivalent cycles occuring during the measurement (or zero for checkups since they
                are not cycled under consistent conditions)
        """
        row = {
            attr: getattr(self, attr)
            for attr in [
                # Inferred from the filename.
                "experiment_id", "number", "type",
                # Features extracted (at least in part) from sensor data
                "calendar_time", "cum_fec", "fec", "missing_sensor_data"]
        }
        row.update(self.meta)
        row.update(self.capacity)
        return row

    def infer_stage(self):
        self.stage = infer_stage(self.file)

    def parse_filename(self):
        words = self.file.stem.split("_")
        self.experiment = "_".join(words[:3])
        self.number = int(words[3])
        self.type = "_".join(words[4:])

    def _meta_file(self):
        m = self.file.parent / (self.file.stem + "_meta.txt")
        if not m.exists():
            print(f"Warning: meta file {m.name} not found")
            return None
        return m
        
    def read_meta(self):
        meta_file = self._meta_file()
        self.meta = {}
        if meta_file is None:
            # We'll just skip with a warning for now...
            return
        with open(meta_file, 'r') as f:
            for line in f:
                if line.startswith("--"):
                    # The rest of the file just depicts the schema of the associated sensor file.
                    break
                words = line.strip().split(": ")
                key = words[0]
                value = ": ".join(words[1:])
                self.meta[key] = value

    def read_sensor_file(self):
        try:
            df = import_datafile(self.file)

            self.run_time_start = df.iloc[0].run_time
            self.capacity = ext.capacity(df)
            # TODO: Correct for erroneous cycles here??
            self.fec = ext.fec_extract(df)
            self.missing_sensor_data = False
        except SensorDataNotFound:
            self.run_time_start = None
            self.capacity = {}
            self.fec = 0
            self.missing_sensor_data = True


    @property
    def measurement_start_time(self) -> Optional[datetime]:
        if "Measurement start date" not in self.meta:
            return None
        start_date = self.meta["Measurement start date"]
        # Manually correct measurement dates that were input improperly:
        correction = MEASUREMENT_CORRECTIONS.get(start_date)
        if correction is not None:
            return correction

        for date_format in ["%d.%m.%Y", "%d.%m.%y"]:
            try:
                return datetime.strptime(start_date, date_format)
            except ValueError:
                continue
        return None

    @property
    def time(self) -> Optional[datetime]:
        """Datetime at which the capacity was measured for checkups, or at which cycling start for cycling measurement."""
        if self.measurement_start_time is None or self.missing_sensor_data:
            return None

        if "t_charge" in self.capacity and not np.isnan(self.capacity["t_charge"]):
            run_time = self.capacity["t_charge"]
        
        else:
            # For cycling.
            run_time = self.run_time_start
        return self.measurement_start_time + timedelta(seconds=run_time)

    def set_experiment_start(self, start_date):
        self.experiment_start = start_date

    @property
    def calendar_time(self):
        """The number of days since the first capacity measurement was taken"""
        if self.experiment_start is None:
            raise ValueError("experiment_start must be set before calendar_time can be assessed.")
        if self.time is None:
            return np.nan
        return (self.time - self.experiment_start).total_seconds()

    def set_cum_fec(self, cum_fec):
        self._cum_fec = cum_fec
        
    @property
    def cum_fec(self):
        if self._cum_fec is None:
            raise ValueError("Must set_cum_fec first.")
        return self._cum_fec
        
        


def group_by_id(measurements: Iterable[Measurement]):
    groups = {}
    for measurement in measurements:
        exp_id = measurement.experiment_id
        if exp_id not in groups:
            groups[exp_id] = [measurement]
        else:
            groups[exp_id].append(measurement)
    return groups


def set_grouped_attributes(measurements: Iterable[Measurement]):
    groups = group_by_id(measurements)

    # set cumulative FEC and experiment start based on experiment groups.
    for experiment_group in groups.values():
        # Sort by measurement number and then calendar time.
        experiment_group.sort(key=lambda m: (m.number, m.time if m.time is not None else datetime(1990, 1, 1)))

        cum_fec = np.cumsum([checkout.fec for checkout in experiment_group])
        for n, checkout in zip(cum_fec, experiment_group):
            checkout.set_experiment_start(experiment_group[0].time)
            checkout.set_cum_fec(n)

        # TODO: Add scheduled measurement time