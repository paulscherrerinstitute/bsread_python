import h5py
import logging

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s - %(message)s')

# The latest h5py user manual is available at - http://docs.h5py.org/en/latest/


class Writer:
    def __init__(self):
        self.file = None
        self.dataset_groups = {}

    def open_file(self, file_name):

        if self.file:
            logger.info('File '+self.file.name+' is currently open - will close it')
            self.close_file()

        logger.info('Open file '+file_name)
        self.file = h5py.File(file_name, "w")

    def close_file(self):
        self.compact_data()

        logger.info('Close file '+self.file.name)
        self.file.close()

    def add_dataset(self, dataset_name, dataset_group_name='data', shape=(1,), dtype="i8", maxshape=(None,), **kwargs):
        """
        Add and create a dataset to the writer.
        :param dataset_name:
        :param shape:
        :param dtype:   b1, i1, i2, i4, i8, u1, u2, u4, u8, f2, f4, f8, c8, c16
                        http://docs.scipy.org/doc/numpy/user/basics.types.html
                        http://docs.scipy.org/doc/numpy/user/basics.rec.html#defining-structured-arrays
        :param maxshape:
        :param kwargs:
        :return:
        """

        if dataset_group_name not in self.dataset_groups:
            self.dataset_groups[dataset_group_name] = DatasetGroup()

        dataset = self.file.require_dataset(dataset_name, shape, dtype=dtype, maxshape=maxshape, **kwargs)
        # chunks=True, shuffle=True, compression="lzf")
        self.dataset_groups[dataset_group_name].datasets.append(Dataset(dataset_name, dataset))

    def add_dataset_stub(self, dataset_group_name='data'):

        if dataset_group_name not in self.dataset_groups:
            self.dataset_groups[dataset_group_name] = DatasetGroup()

        self.dataset_groups[dataset_group_name].datasets.append(None)

    def write(self, data, dataset_group_name='data'):
        """
        Write data to datasets. It is mandatory that the size of the data list is the same as the datasets
        :param data: List of values to write to the configured datasets
        """

        if dataset_group_name not in self.dataset_groups:
            raise RuntimeError('Cannot write data, dataset group '+dataset_group_name+' does not exist')

        dataset_group = self.dataset_groups[dataset_group_name]

        if len(data) != len(dataset_group.datasets):
            raise RuntimeError('The size of the passed data object does not match the size of datasets configured')

        # Write to dataset
        for index, dataset in enumerate(dataset_group.datasets):
            if dataset:  # Check for dataset stub, i.e. None
                required_size = dataset.count + 1
                if dataset.reference.shape[0] < required_size:
                    dataset.reference.resize(dataset.count + 1000, axis=0)
                # TODO need to add an None check - i.e. for different frequencies
                # ADD else clause
                if data is not None and data[index] is not None:
                    dataset.reference[dataset.count] = data[index]

                dataset.count += 1

    def compact_data(self):
        """Compact datasets, i.e. shrink them to actual size"""

        for key, dataset_group in self.dataset_groups.items():
            for dataset in dataset_group.datasets:
                if dataset:  # Check for dataset stub, i.e. None
                    # Compact if count is smaller than actual size
                    if dataset.count < dataset.reference.shape[0]:
                        logger.info('Compact data for dataset '+dataset.name + ' from '+str(dataset.reference.shape[0])+' to ' + str(dataset.count))
                        dataset.reference.resize(dataset.count, axis=0)


class Dataset:
    def __init__(self, name, dataset_reference, count=0):
        self.name = name
        self.count = count
        self.reference = dataset_reference


class DatasetGroup:
    def __init__(self):
        self.datasets = []


# Example writer
if __name__ == "__main__":
    writer = Writer()

    writer.open_file('test.h5')
    writer.add_dataset('/test/data')

    for number in range(0, 100):
        writer.write([number])

    writer.close_file()
