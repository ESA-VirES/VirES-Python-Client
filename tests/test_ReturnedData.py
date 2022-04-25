import pytest
import os
import pandas

from viresclient._data_handling import ReturnedDataFile, ReturnedData

SUPPORTED_FILETYPES = ('csv', 'cdf', 'nc')

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# # Test data generated from:
# request = SwarmRequest(...)
# request.set_collection("SW_OPER_MAGA_LR_1B")
# request.set_products(measurements=["F","B_NEC"],
#                      sampling_step="PT10S")
# request.set_range_filter(parameter="Latitude",
#                          minimum=0,
#                          maximum=90)
# data = request.get_between(start_time=dt.datetime(2016,1,1),
#                            end_time=dt.datetime(2016,1,1,1), filetype="cdf")
TEST_FILES = {
    "cdf": os.path.join(TEST_DATA_DIR, "test_data_01.cdf"),
    "csv": os.path.join(TEST_DATA_DIR, "test_data_01.csv"),
    "json_from_cdf": os.path.join(TEST_DATA_DIR, "test_data_01_from_cdf.json")
}


def test_ReturnedDataFile_setup():
    """Test setup of ReturnedDataFile objects

    Enforcement of filetype as 'csv'/'cdf'/'nc' (lower case)
    """
    # CSV/CDF/NC should be converted to csv/cdf/nc
    for filetype in SUPPORTED_FILETYPES:
        retdata = ReturnedDataFile(filetype=filetype.upper())
        assert retdata.filetype == filetype
        retdata = ReturnedDataFile(filetype=filetype)
        assert retdata.filetype == filetype

    # The following should raise a TypeError:
    #  filetype must be csv/cdf/nc
    with pytest.raises(TypeError):
        retdata = ReturnedDataFile(filetype='xyz')
    with pytest.raises(TypeError):
        retdata = ReturnedDataFile(filetype=1)


def test_ReturnedData_setup():
    """Test setup of ReturnedData objects

    Enforcement of filetype as 'csv'/'cdf'/'nc' (lower case)
    """
    # CSV/CDF/NC should be converted to csv/cdf/nc
    for filetype in SUPPORTED_FILETYPES:
        retdata = ReturnedData(filetype=filetype.upper())
        assert retdata.filetype == filetype
        retdata = ReturnedData(filetype=filetype)
        assert retdata.filetype == filetype

    # The following should raise a TypeError:
    #  filetype must be csv/cdf/nc
    with pytest.raises(TypeError):
        retdata = ReturnedData(filetype='xyz')
    with pytest.raises(TypeError):
        retdata = ReturnedData(filetype=1)


def test_ReturnedDataFile_saving(tmpfile):
    """Test saving of ReturnedDataFile

    Writing files with extension checking
    Dealing correctly with overwrite or not
    """
    for filetype in SUPPORTED_FILETYPES:

        # Check that file name and extension checking is enforced
        retdata = ReturnedDataFile(filetype=filetype)
        retdata._write_new_data(b'testtext')
        with pytest.raises(TypeError):
            retdata.to_file(1)
        with pytest.raises(TypeError):
            retdata.to_file(
                str(tmpfile("testfile.xyz"))
                )

        # Check that not overwriting and overwriting work right
        testfile = str(tmpfile('testfile.{}'.format(filetype)))
        retdata.to_file(testfile)
        # with pytest.raises(FileExistsError):  # not in py27
        with pytest.raises(Exception):
            retdata.to_file(
                testfile, overwrite=False
                )
        retdata.to_file(
            testfile, overwrite=True
            )


def test_ReturnedData_saving(tmpfile):
    """Test saving of ReturnedData (single file case only)

    Writing files with extension checking
    Dealing correctly with overwrite or not
    """
    for filetype in SUPPORTED_FILETYPES:

        # Check that file name and extension checking is enforced
        retdata = ReturnedData(filetype=filetype)
        retdata.contents[0]._write_new_data(b'testtext')
        with pytest.raises(TypeError):
            retdata.to_file(1)
        with pytest.raises(TypeError):
            retdata.to_file(
                str(tmpfile("testfile.xyz"))
                )
        # Repeat for .to_files()
        with pytest.raises(TypeError):
            retdata.to_files([1])
        with pytest.raises(TypeError):
            retdata.to_files(
                [str(tmpfile("testfile.xyz"))]
                )

        # Check that not overwriting and overwriting work right
        testfile = str(tmpfile('testfile.{}'.format(filetype)))
        retdata.to_file(testfile)
        # with pytest.raises(FileExistsError):  # not in py27
        with pytest.raises(Exception):
            retdata.to_file(
                testfile, overwrite=False
                )
        retdata.to_file(
            testfile, overwrite=True
            )
        # repeat for .to_files()
        testfile = str(tmpfile('testfile2.{}'.format(filetype)))
        retdata.to_files([testfile])
        with pytest.raises(Exception):
            retdata.to_files(
                [testfile], overwrite=False
                )
        retdata.to_files(
            [testfile], overwrite=True
            )


def test_ReturnedDataFile_dataframe():
    """Test ReturnedDataFile dataframe generation

    Compare generated dataframe with the example file
    Load dataframes from equivalent cdf and csv files.
    Check that the index and column labels match.
    Check that they also match the expected output (in json file).

    """
    # Initalise objects from the stored test data
    data_cdf = ReturnedDataFile(filetype="cdf")
    data_csv = ReturnedDataFile(filetype="csv")
    with open(TEST_FILES["cdf"], "rb") as f:
        data_cdf._write_new_data(f.read())
    with open(TEST_FILES["csv"], "rb") as f:
        data_csv._write_new_data(f.read())
    df_cdf = data_cdf.as_dataframe()
    df_csv = data_csv.as_dataframe()
    # Check equivalency of dataframes loaded from cdf and csv
    assert df_cdf.index.equals(df_csv.index)
    assert set(df_cdf.keys()) == set(df_csv.keys())
    # assert df_cdf.equals(df_csv)
    # Check equivalency to the pre-made dataframe
    df_json = pandas.read_json(TEST_FILES["json_from_cdf"])
    assert df_cdf.index.equals(df_json.index)
    assert set(df_cdf.keys()) == set(df_json.keys())


def test_ReturnedData_dataframe():
    """Test ReturnedData dataframe generation (single file case only)

    Compare generated dataframe with the example file
    Load dataframes from equivalent cdf and csv files.
    Check that the index and column labels match.
    Check that they also match the expected output (in json file).

    """
    # Initalise objects from the stored test data
    data_cdf = ReturnedData(filetype="cdf")
    data_csv = ReturnedData(filetype="csv")
    with open(TEST_FILES["cdf"], "rb") as f:
        data_cdf.contents[0]._write_new_data(f.read())
    with open(TEST_FILES["csv"], "rb") as f:
        data_csv.contents[0]._write_new_data(f.read())
    df_cdf = data_cdf.as_dataframe()
    df_csv = data_csv.as_dataframe()
    # Check equivalency of dataframes loaded from cdf and csv
    assert df_cdf.index.equals(df_csv.index)
    assert set(df_cdf.keys()) == set(df_csv.keys())
    # assert df_cdf.equals(df_csv)
    # Check equivalency to the pre-made dataframe
    df_json = pandas.read_json(TEST_FILES["json_from_cdf"])
    assert df_cdf.index.equals(df_json.index)
    assert set(df_cdf.keys()) == set(df_json.keys())


def test_ReturnedDataFile_xarray():
    """Test ReturnedDataFile xarray generation

    Check that xarray keys and index match that from the dataframe

    """
    # Initalise objects from the stored test data
    data_cdf = ReturnedDataFile(filetype="cdf")
    with open(TEST_FILES["cdf"], "rb") as f:
        data_cdf._write_new_data(f.read())
    ds = data_cdf.as_xarray()
    # Check equivalency to the pre-made dataframe
    df_json = pandas.read_json(TEST_FILES["json_from_cdf"])
    # NB Since xarray v0.11.0, Dataset keys no longer includes "Timestamp"
    assert set(ds.keys()) == set(df_json.keys())
    assert ds.indexes["Timestamp"].equals(df_json.index)


def test_ReturnedData_xarray():
    """Test ReturnedData xarray generation (single file case only)

    Check that xarray keys and index match that from the dataframe

    """
    # Initalise objects from the stored test data
    data_cdf = ReturnedData(filetype="cdf")
    with open(TEST_FILES["cdf"], "rb") as f:
        data_cdf.contents[0]._write_new_data(f.read())
    ds = data_cdf.as_xarray()
    # Check equivalency to the pre-made dataframe
    df_json = pandas.read_json(TEST_FILES["json_from_cdf"])
    # NB Since xarray v0.11.0, Dataset keys no longer includes "Timestamp"
    assert set(ds.keys()) == set(df_json.keys())
    assert ds.indexes["Timestamp"].equals(df_json.index)
