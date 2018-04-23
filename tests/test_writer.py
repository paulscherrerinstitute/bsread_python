import unittest

import os

import h5py

from bsread.writer import Writer


class TestWriter(unittest.TestCase):

    TEST_FILENAME = "ignore_test.h5"

    def tearDown(self):
        try:
            os.remove(self.TEST_FILENAME)
        except:
            pass

    def test_basic_workflow(self):
        writer = Writer()

        writer.open_file(self.TEST_FILENAME)
        writer.add_dataset("/test/data")

        for number in range(0, 100):
            writer.write([number])

        writer.close_file()

        file = h5py.File(self.TEST_FILENAME)

        self.assertIsNotNone(file.get("/test/data"))

        file.close()

    def test_stub_datasets(self):
        writer = Writer()

        writer.open_file(self.TEST_FILENAME)
        writer.add_dataset("/test/data")
        writer.add_dataset_stub(dataset_name="fake_dataset")

        for number in range(0, 100):
            writer.write([number, None])

        writer.close_file()

        file = h5py.File(self.TEST_FILENAME)

        self.assertIsNotNone(file.get("/test/data"))

        file.close()

    def test_stub_replacement(self):
        writer = Writer()

        writer.open_file(self.TEST_FILENAME)

        writer.add_dataset("/test/data")
        writer.add_dataset_stub(dataset_name="/test/data2")

        for number in range(0, 50):
            writer.write([number, number])

        writer.replace_dataset(dataset_name="/test/data2")

        for number in range(50, 100):
            writer.write([number, number])

        writer.close_file()

        file = h5py.File(self.TEST_FILENAME)

        self.assertIsNotNone(file.get("/test/data"))

        new_dataset = file.get("/test/data2")

        self.assertIsNotNone(new_dataset)
        self.assertEqual(len(new_dataset), 100)
        self.assertListEqual(list(new_dataset[0:50]), [0] * 50)
        self.assertListEqual(list(new_dataset[50:100]), list(range(50, 100)))

        file.close()

    def test_dataset_replacement(self):
        writer = Writer()

        writer.open_file(self.TEST_FILENAME)

        writer.add_dataset("/test/data")
        writer.add_dataset("/test/data_replace")

        for number in range(0, 50):
            writer.write([number, number])

        writer.replace_dataset(dataset_name="/test/data_replace")

        for number in range(50, 100):
            writer.write([number, number])

        writer.close_file()

        file = h5py.File(self.TEST_FILENAME)

        self.assertIsNotNone(file.get("/test/data"))
        self.assertIsNotNone(file.get("/test/data_replace"))

        new_dataset = file.get("/test/data_replace")
        replaced_dataset = file.get("/test/data_replace(1)")

        self.assertIsNotNone(new_dataset)
        self.assertEqual(len(new_dataset), 100)
        self.assertListEqual(list(new_dataset[0:50]), [0] * 50)
        self.assertListEqual(list(new_dataset[50:100]), list(range(50, 100)))

        self.assertIsNotNone(replaced_dataset)
        self.assertEqual(len(replaced_dataset), 50)
        self.assertListEqual(list(replaced_dataset[0:50]), list(range(0, 50)))

        file.close()

    def test_multiple_dataset_replacements(self):
        writer = Writer()

        writer.open_file(self.TEST_FILENAME)

        writer.add_dataset("/test/data")
        writer.add_dataset("/test/data_replace")

        for number in range(0, 50):
            writer.write([number, number])

        writer.replace_dataset(dataset_name="/test/data_replace")
        writer.replace_dataset(dataset_name="/test/data_replace")
        writer.replace_dataset(dataset_name="/test/data_replace")

        for number in range(50, 100):
            writer.write([number, number])

        writer.close_file()

        file = h5py.File(self.TEST_FILENAME)

        self.assertIsNotNone(file.get("/test/data"))
        self.assertIsNotNone(file.get("/test/data_replace"))

        new_dataset = file.get("/test/data_replace")
        replaced_dataset_1 = file.get("/test/data_replace(1)")
        replaced_dataset_2 = file.get("/test/data_replace(2)")
        replaced_dataset_3 = file.get("/test/data_replace(3)")

        self.assertIsNotNone(new_dataset)
        self.assertIsNotNone(replaced_dataset_1)
        self.assertIsNotNone(replaced_dataset_2)
        self.assertIsNotNone(replaced_dataset_3)

        self.assertListEqual(list(new_dataset[50:100]), list(range(50, 100)))
        self.assertListEqual(list(replaced_dataset_1), list(range(50)))
        self.assertListEqual(list(replaced_dataset_2), [0] * 50)
        self.assertListEqual(list(replaced_dataset_3), [0] * 50)

        file.close()
