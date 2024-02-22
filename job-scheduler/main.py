import os
from google.cloud import bigquery
from google.cloud import storage
import pandas as pd
import re

from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["POST"])
def index():
    """Receive and parse Pub/Sub messages."""
    
    project_id = os.environ.get('PROJECT_ID')
    dataset_id = os.environ.get('DATASET_ID')
    raw_target_table = os.environ.get('RAW_TARGET_TABLE')
    target_table = os.environ.get('TARGET_TABLE')
    raw_source_tables = ["source-uipetmis","source-uispet"] #os.environ.get('RAW_SOURCE_TABLES')
    raw_source_tables_wildcard = os.environ.get('RAW_SOURCE_TABLES_WILDCARD')
    source_table = os.environ.get('SOURCE_TABLE')
    queued_jobs_bucket_name = os.environ.get('QUEUED_JOBS_BUCKET_NAME')

    print(f"env vars: queued_jobs_bucket_name={queued_jobs_bucket_name}, project_id={project_id}, dataset_id={dataset_id}, raw_target_table={raw_target_table}, target_table={target_table}, raw_source_tables={raw_source_tables}, raw_source_tables_wildcard={raw_source_tables_wildcard}, source_table={source_table}")
    
    msg = ""
    envelope = request.get_json()
    if not envelope:
        msg = "no Pub/Sub message received"
        print(msg)
        return (f"Completed Request: {msg}", 204)

    if not isinstance(envelope, dict) or "message" not in envelope:
        msg = "invalid Pub/Sub message format"
        print(msg)
        return (f"Completed Request: {msg}", 204)

    pubsub_message = envelope["message"]

    if not isinstance(pubsub_message, dict) or "attributes" not in pubsub_message:
        msg = "invalid Pub/Sub message format - no attributes!"
        print(msg)
        return (f"Completed Request: {msg}", 204)
    
    pubsub_message_attributes = envelope["message"]["attributes"]

    if not isinstance(pubsub_message_attributes, dict) and "bucketId" in pubsub_message_attributes and "objectId" in pubsub_message_attributes:
        msg = "bucketId and objectId are not both found in the PubSub message attributes!"
        print(msg)
        return (f"Completed Request: {msg}", 204)
    
    bucketId = pubsub_message_attributes['bucketId']
    objectId = pubsub_message_attributes['objectId']
    
    pattern = r"^jobs_per_target_row-(\d{1,4})-min_group_size-(\d{1,4})-maximum_fields_per_request-(\d{1,4})$"
    match = re.match(pattern, objectId)
    if not match:
        msg = "objectId is not in the expected format: ^jobs_per_target_row-(\d{1,4})-min_group_size-(\d{1,4})-maximum_fields_per_request-(\d{1,4})$"
        print(msg)
        return (f"Completed Request: {msg}", 204)
    
    jobs_per_target_row = int(match.group(1))
    min_group_size = int(match.group(2))
    maximum_fields_per_request = int(match.group(3))

    print(f"*********************************************************************")
    print(f"*Valid job request recieved: bucket {bucketId}, object {objectId}*")
    print(f"*********************************************************************")
    print(f"*Job details:*")
    print(f"*jobs_per_target_row:{jobs_per_target_row}*")
    print(f"*min_group_size:{min_group_size}*")
    print(f"*maximum_fields_per_request:{maximum_fields_per_request}*")
    print(f"*********************************************************************")

    storage_client = storage.Client()
    jobs_bucket = storage_client.bucket(bucketId)
    blob = jobs_bucket.blob(objectId)

    if not blob.exists():
        print(f"File '{objectId}' not found in bucket '{bucketId}'. Job already in process or completed. Container instance completing with 204 message")
        return ("", 204)

    client = bigquery.Client(project=project_id)

    def add_unique_ref_and_create_new_table(project_id, dataset_id, raw_table, new_table, new_col, prefix):
        """Adds 'Source_Unique_Ref' column if missing, then creates a new BigQuery table.

        Args:
            project_id: BigQuery project ID.
            dataset_id: BigQuery dataset ID.
            raw_tables: Dict containing raw table names
            new_table: Desired name of finalised table
            new_col: the name of the reference column for the table
        """

        raw_query = f"""
            SELECT *  
            FROM `{project_id}.{dataset_id}.{raw_table}`
        """
        raw_df = client.query(raw_query).to_dataframe()

        # Rename columns with prefix
        for col in raw_df.columns:
            print(f"col is {col}")
            if col != f"Unique_Ref":
                print(f"therefore renaming {col} to {prefix}_{col}")
                raw_df.rename(columns={col: f"{prefix}_{col}"}, inplace=True)
            else:
                print(f"therefore renaming {col} to Original_{col}")
                raw_df.rename(columns={col: f"Original_{col}"}, inplace=True)

        raw_df[new_col] = range(1, len(raw_df) + 1)
        
        new_table_id = f"{project_id}.{dataset_id}.{new_table}"

        job_config = bigquery.LoadJobConfig()  
        job = client.load_table_from_dataframe(raw_df, new_table_id, job_config=job_config)
        job.result()

        return job.result()
    
    # Source table setup
    source_table_ref = client.dataset(dataset_id).table(source_table) 
    try:
        client.get_table(source_table_ref)  # Will raise NotFound if the table doesn't exist
        print("Source table '{}' exists.".format(source_table))
    except:
        print(f"Source table {source_table} does not exist. Creating Source table...")
        new_source_col = 'Source_Unique_Ref'
        source_prefix = "Source"   
        add_unique_ref_and_create_new_table(project_id, dataset_id, raw_source_tables_wildcard, source_table, new_source_col, source_prefix)

    source_query = f"SELECT * FROM `{project_id}.{dataset_id}.{source_table}`"
    source_df = client.query(source_query).to_dataframe()
    print(f"source_df length is {source_df.shape[0]}")


    # Target table setup
    target_table_ref = client.dataset(dataset_id).table(target_table) 
    try:
        client.get_table(target_table_ref)  # Will raise NotFound if the table doesn't exist
        print(f"Target table {target_table} exists.")
    except:
        print(f"Target table {target_table} does not exist. Creating Target table...")
        new_target_col = 'Target_Unique_Ref'
        target_prefix = "Target"   
        add_unique_ref_and_create_new_table(project_id, dataset_id, raw_target_table, target_table, new_target_col, target_prefix)

    target_query = f" SELECT * FROM `{project_id}.{dataset_id}.{target_table}`"
    target_df = client.query(target_query).to_dataframe()
    print(f"target_df length is {target_df.shape[0]}")

    def create_df_groups(df, grouping_levels):
        """Groups a DataFrame by nested schema paths up to a specified level.

        Args:
            df: The DataFrame to group.

        Returns:
            A dictionary of DataFrames, where keys are the nested paths, and
            values are DataFrames containing fields sharing that path. 
        """

        grouped_dfs = {}

        for _, row in df.iterrows():
            path = '.'.join(row[col] for col in grouping_levels)
            if path not in grouped_dfs:
                grouped_dfs[path] = pd.DataFrame(columns=df.columns)  
            grouped_dfs[path] = pd.concat([grouped_dfs[path], row.to_frame().T], ignore_index=True)

        return grouped_dfs

    def dataframe_to_string(df):
        """Converts a DataFrame to a string with column names and row values.

        Args:
            df: The pandas DataFrame to convert.

        Returns:
            A string representation of the DataFrame.
        """

        output = f"Column Names: {', '.join(df.columns)}\n"  # Header with column names

        for _, row in df.iterrows():
            row_string = ', '.join(str(value) for value in row)
            output += f"Row: {row_string}\n"

        return output

    def chop_source_df_groups(source_df_groups, max_rows_per_group):
        """Chops source dataframe groups into smaller groups with a specified max number of rows.

        Args:
            source_df_groups: The dictionary of source dataframe groups.
            max_rows_per_group: The maximum number of rows allowed in each group.

        Returns:
            A modified dictionary of source dataframe groups with smaller groups.
        """
        chopped_source_df_groups = {}

        for path, source_group_df in source_df_groups.items():
            # Check if the group needs to be chopped
            if len(source_group_df) <= max_rows_per_group:
                chopped_source_df_groups[path] = source_group_df
            else:
                # Split the group into smaller groups with a maximum of max_rows_per_group rows
                num_subgroups = len(source_group_df) // max_rows_per_group
                remainder = len(source_group_df) % max_rows_per_group

                for i in range(num_subgroups):
                    start_idx = i * max_rows_per_group
                    end_idx = (i + 1) * max_rows_per_group
                    sub_df = source_group_df.iloc[start_idx:end_idx]
                    chopped_source_df_groups[f"{path}_subgroup_{i+1}"] = sub_df

                # Add the remainder as a separate subgroup
                if remainder > 0:
                    sub_df = source_group_df.iloc[-remainder:]
                    chopped_source_df_groups[f"{path}_subgroup_{num_subgroups+1}"] = sub_df

        return chopped_source_df_groups


    def merge_source_df_groups(source_df_groups, max_rows_per_group):
        """Chops source dataframe groups and combines smaller groups.

        Args:
            source_df_groups: The dictionary of source dataframe groups.
            max_rows_per_group: The maximum number of rows allowed in each group.

        Returns:
            A modified dictionary of source dataframe groups with optimized sizing.
        """
        chopped_source_df_groups = {}
        group_paths = list(source_df_groups.keys())  # Get a list of group paths for iteration

        i = 0
        while i < len(group_paths):
            current_path = group_paths[i]
            current_group_df = source_df_groups[current_path]
                
            # Combine with subsequent groups while possible
            while i + 1 < len(group_paths) and len(current_group_df) + len(source_df_groups[group_paths[i + 1]]) <= max_rows_per_group:
                next_path = group_paths[i + 1]
                next_group_df = source_df_groups[next_path]
                current_group_df = pd.concat([current_group_df, next_group_df], ignore_index=True)
                del source_df_groups[next_path]  # Remove the merged group
                group_paths.pop(i + 1)  # Update the list of group paths

            # Add the combined (or original) group
            chopped_source_df_groups[current_path] = current_group_df
            i += 1

        return chopped_source_df_groups

    def merge_small_groups(chopped_source_df_groups, min_group_size):
        """Merges small groups (length < min_group_size) with their preceding groups.

        Args:
            chopped_source_df_groups: The dictionary of chopped dataframe groups.
            min_group_size: min group size allowed (smaller than this is merged with preceding group)

        Returns:
            A modified dictionary of dataframe groups with fewer small groups.
        """
        group_paths = list(chopped_source_df_groups.keys())
        i = 1  # Start from the second group
        while i < len(group_paths):
            current_path = group_paths[i]
            current_group_df = chopped_source_df_groups[current_path]

            if len(current_group_df) < min_group_size:
                prev_path = group_paths[i - 1]
                prev_group_df = chopped_source_df_groups[prev_path]

                # Merge with the previous group
                chopped_source_df_groups[prev_path] = pd.concat([prev_group_df, current_group_df], ignore_index=True)

                # Remove the current group
                del chopped_source_df_groups[current_path]
                group_paths.pop(i) 
            else:
                i += 1

        return chopped_source_df_groups
    

    source_grouping_levels = [f"Source_SchemaName", f"Source_TableName"]
    source_df_groups = create_df_groups(source_df, source_grouping_levels)

    source_string_groups = []
    for path, source_group_df in source_df_groups.items():
        source_group_sting = dataframe_to_string(source_group_df)
        source_string_groups.append(source_group_sting)
        
    print(f"Number of source schema dataframe groupings: {len(source_df_groups)}")
    print(f"Number of source schema string groupings: {len(source_string_groups)}\n")

    #Further split up the source_df_groups to make sure there is no group larger than maximum_fields_per_request variable. This prevents LLM innacuacies when the number of requested field mappings is too high.
    chopped_source_df_groups = chop_source_df_groups(source_df_groups, maximum_fields_per_request)
    print(f"Number of chopped source schema dataframe groupings: {len(chopped_source_df_groups)}")
    chopped_length_counts = {}
    for group_df in chopped_source_df_groups.values():
        group_length = len(group_df)
        if group_length in chopped_length_counts:
            chopped_length_counts[group_length] += 1
        else:
            chopped_length_counts[group_length] = 1
    print(f"Distribution of chopped lengths:")
    for length, count in chopped_length_counts.items():
        print(f"{count} x groups with length {length}")


    #Merge groups in cases where adjascent groups could be merged together and still fit below the maximum_fields_per_request variable.
    merged_source_df_groups = merge_source_df_groups(chopped_source_df_groups, maximum_fields_per_request)
    print(f"\nNumber of merged source schema dataframe groupings: {len(merged_source_df_groups)}")
    merged_length_counts = {}
    for group_df in merged_source_df_groups.values():
        group_length = len(group_df)
        if group_length in merged_length_counts:
            merged_length_counts[group_length] += 1
        else:
            merged_length_counts[group_length] = 1
    print(f"Distribution of merged lengths:")
    for length, count in merged_length_counts.items():
        print(f"{count} x groups with length {length}")



    #To remove small groups, merge together groups when the group adjascent group is equal or less than , reglardless of maximum_fields_per_request variable.
    combined_source_df_groups = merge_small_groups(merged_source_df_groups, min_group_size)
    print(f"\nNumber of combined source schema dataframe groupings: {len(combined_source_df_groups)}")

    combined_length_counts = {}
    for group_df in combined_source_df_groups.values():
        group_length = len(group_df)
        if group_length in combined_length_counts:
            combined_length_counts[group_length] += 1
        else:
            combined_length_counts[group_length] = 1
    print(f"Distribution of combined lengths:")
    for length, count in combined_length_counts.items():
        print(f"{count} x groups with length {length}")



    print("\nconverting dataframe groupings to string groupings...")
    combined_source_string_groups = []
    for path, combined_source_df_group in combined_source_df_groups.items():
        combined_source_string_group = dataframe_to_string(combined_source_df_group)
        combined_source_string_groups.append(combined_source_string_group)
    print(f"...Complete. Number of combined source schema string groupings: {len(combined_source_string_groups)}\n")



    def split_into_jobs(combined_source_string_groups, number_jobs_per_target_row):
        """Splits a list into jobs and returns a string blob containing all the source string groups for a job.

        Args:
            combined_source_string_groups: The list to be split into jobs.
            number_jobs_per_target_row: The desired number of jobs.

        Returns:
            A list of strings, where each string represents a job.
        """

        list_length = len(combined_source_string_groups)
        items_per_job = list_length // number_jobs_per_target_row
        remainder = list_length % number_jobs_per_target_row

        jobs = []
        for target_row_num in range(target_df.shape[0]):
            start_index = 0
            for job_num in range(number_jobs_per_target_row):
                end_index = start_index + items_per_job
                if job_num < remainder:  # Distribute remainder items across initial jobs
                    end_index += 1
                    
                job_content = ""
                for index in range(start_index,end_index):
                    job_content += f"""{combined_source_string_groups[index]}\n"""
                job_name = f"target-row-{target_row_num}-source-groups-{start_index}-{end_index}"
                jobs.append({'job_name': job_name, 'job_content': job_content})
                start_index = end_index

        return jobs
    
    jobs_list = split_into_jobs(combined_source_string_groups, jobs_per_target_row)

    def upload_jobs_to_queue(jobs_list, bucket_name):
        """Iterates over a list and uploads items as objects to Google Cloud Storage.

        Args:
            data_list: The list of items to upload as object contents.
            bucket_name: The name of the Google Cloud Storage bucket.
        """

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        for index, item in enumerate(jobs_list):

            blob = bucket.blob(item['job_name'])

            try:
                # Use an in-memory buffer for smaller data
                blob.upload_from_string(item['job_content'])  
                print(f"Uploaded {item['job_name']} successfully.")
            except Exception as e:
                print(f"Error uploading {item['job_name']}: {e}")

    upload_jobs_to_queue(jobs_list, queued_jobs_bucket_name)



    blob.delete()
    print(f"Job scheduling complete. File '{objectId}' removed from bucket '{bucketId}'.")

    print(f"*********************************************************************")
    print(f"*Jobs summary*")
    print(f"*********************************************************************")
    print(f"*Target rows:{target_df.shape[0]}*")
    print(f"*Source field groups:{len(combined_source_string_groups)}*")
    print(f"*Total requests to Gemini:{target_df.shape[0]*len(combined_source_string_groups)}*")
    print(f"")
    print(f"Which have been split into jobs:")
    print(f"Total jobs: {len(jobs_list)}")
    print(f"*Jobs per target row:{jobs_per_target_row}*")
    print(f"Av. Source field groups (=Av. requests to Gemini) per job:{(target_df.shape[0]*len(combined_source_string_groups))/len(jobs_list)}")

    print(f"*********************************************************************")


    return (f"Successful Request", 204)