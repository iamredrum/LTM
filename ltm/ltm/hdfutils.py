'''
Created on May 9, 2018

@author: dgrewal
'''
import pandas as pd


def concat_csvs_to_hdf(infiles, outfile, tablenames):
    with pd.HDFStore(outfile, 'w', complevel=9, complib='blosc') as output:
        for infile, tablename in zip(infiles, tablenames):
            df = pd.read_csv(infile)

            output.put(tablename, df)


def merge_csvs_to_hdf_in_memory(infiles, outfile, tablename):

    data = [pd.read_csv(infile) for infile in infiles]

    data = pd.concat(data)

    with pd.HDFStore(outfile, 'w', complevel=9, complib='blosc') as output:
        output.put(tablename, data)


def merge_csvs_to_hdf_on_disk(infiles, outfile, tablename):

    with pd.HDFStore(outfile, 'w', complevel=9, complib='blosc') as output:

        for infile in infiles:
            data = pd.read_csv(infile)

            if tablename not in output:
                output.put(tablename, data, format='table')
            else:
                output.append(tablename, data, format='table')


def convert_csv_to_hdf(infile, outfile, tablename):
    df = pd.read_csv(infile, dtype = {'chr': str})

    df = df.infer_objects()

    with pd.HDFStore(outfile, 'w', complevel=9, complib='blosc') as out_store:
        out_store.put(tablename, df, format='table')


def merge_cells_in_memory(
        hdf_input, output_store_obj, tablename,
        tables_to_merge=None, dtypes={}):
    data = []

    with pd.HDFStore(hdf_input, 'r') as input_store:
        if not tables_to_merge:
            tables_to_merge = input_store.keys()

        for tableid in tables_to_merge:
            data.append(input_store[tableid])

    data = pd.concat(data)
    data = data.reset_index()

    for col, dtype in dtypes.iteritems():
        data[col] = data[col].astype(dtype)

    output_store_obj.put(tablename, data, format="table")


def merge_cells_on_disk(
        hdf_input, output_store_obj, tablename,
        tables_to_merge=None, dtypes={}):

    with pd.HDFStore(hdf_input, 'r') as input_store:

        if not tables_to_merge:
            tables_to_merge = input_store.keys()

        for tableid in tables_to_merge:
            celldata = input_store[tableid]

            for col, dtype in dtypes.iteritems():
                celldata[col] = celldata[col].astype(dtype)

            if tablename not in output_store_obj:
                output_store_obj.put(tablename, celldata, format='table')
            else:
                output_store_obj.append(tablename, celldata, format='table')


def merge_per_cell_tables(
        infile, output, out_tablename,
        tables_to_merge=None, in_memory=True, dtypes={}):

    if isinstance(output, pd.HDFStore):
        output_store = output
    else:
        output_store = pd.HDFStore(output, 'w', complevel=9, complib='blosc')

    if in_memory:
        merge_cells_in_memory(
            infile,
            output_store,
            out_tablename,
            tables_to_merge=tables_to_merge,
            dtypes=dtypes)
    else:
        merge_cells_on_disk(
            infile,
            output_store,
            out_tablename,
            tables_to_merge=tables_to_merge,
            dtypes=dtypes)

    if not isinstance(output, pd.HDFStore):
        output_store.close()


def annotate_per_cell_store_with_dict(infile, annotation_data, output):
    """
    adds new cols to dataframes in store from a dictionary
    store must be split by cells (no tables with all cells merged together)
    annotation_data must be 2 level dict with cellid as first key,
    colnames as second, values for cols as leaves

    """
    with pd.HDFStore(output, 'w', complevel=9, complib='blosc') as output, pd.HDFStore(infile) as input_store:
        for tableid in input_store.keys():
            data = input_store[tableid]

            cell_id = data["cell_id"].iloc[0]

            cell_info = annotation_data[cell_id]

            for colname, value in cell_info.iteritems():
                data[colname] = value

                output.put(tableid, data, format="table")


def annotate_store_with_dict(infile, annotation_data, output, tables=None):
    """
    adds new cols to dataframes in store from a dictionary
    """

    if isinstance(output, pd.HDFStore):
        output_store = output
    else:
        output_store = pd.HDFStore(output, 'w', complevel=9, complib='blosc')

    if isinstance(infile, pd.HDFStore):
        input_store = infile
    else:
        input_store = pd.HDFStore(infile, 'r')

    if not tables:
        tables = input_store.keys()

    for tableid in tables:
        data = input_store[tableid]

        cells = data["cell_id"].unique()

        for cellid in cells:
            cell_info = annotation_data[cellid]
            for colname, value in cell_info.iteritems():
                data.loc[data["cell_id"] == cellid, colname] = value

        output_store.put(tableid, data, format="table")

    if not isinstance(output, pd.HDFStore):
        output_store.close()

    if not isinstance(input, pd.HDFStore):
        input_store.close()