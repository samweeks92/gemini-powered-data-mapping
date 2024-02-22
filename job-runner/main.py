import os
from google.cloud import bigquery
from google.cloud import storage
import pandas as pd
from vertexai.preview import generative_models
from vertexai.preview.generative_models import GenerativeModel
import re
import time

from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["POST"])
def index():
    """Receive and parse Pub/Sub messages."""
    
    project_id = os.environ.get('PROJECT_ID')
    dataset_id = os.environ.get('DATASET_ID')

    target_table = os.environ.get('TARGET_TABLE')
    mapped_table = os.environ.get('MAPPED_TABLE')

    source_table = os.environ.get('SOURCE_TABLE')

    in_progress_jobs_bucket_name = os.environ.get('IN_PROGRESS_JOBS_BUCKET_NAME')
    completed_jobs_bucket_name = os.environ.get('COMPLETED_JOBS_BUCKET_NAME')
    failed_jobs_bucket_name = os.environ.get('FAILED_JOBS_BUCKET_NAME')
    bq_upload_queue_bucket_name = os.environ.get('BQ_UPLOAD_QUEUE_BUCKET_NAME')
    
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

    storage_client = storage.Client()
    queued_jobs_bucket = storage_client.bucket(bucketId)
    in_progress_jobs_bucket = storage_client.bucket(in_progress_jobs_bucket_name)
    bq_upload_queue_bucket = storage_client.bucket(bq_upload_queue_bucket_name)
    completed_jobs_bucket = storage_client.bucket(completed_jobs_bucket_name)  
    failed_jobs_bucket = storage_client.bucket(failed_jobs_bucket_name)

    queued_blob = queued_jobs_bucket.blob(objectId)
    
    get_job_object_retries=3
    for attempt in range(get_job_object_retries):
        queued_blob = queued_jobs_bucket.blob(objectId)
        if queued_blob.exists():
            break  # Exit the loop if the blob is found
        print(f"File {objectId} not found in bucket {bucketId} (attempt {attempt+1}/{get_job_object_retries})...")
        time.sleep(1+attempt)

    if not queued_blob.exists():  
        print(f"File '{objectId}' not found in bucket '{bucketId}'. Job already picked from queue. Container instance completing with 204 message")
        return ("", 204)      
          
    
    pattern = r"^target-row-(\d{1,4})-source-groups-(\d{1,4})-(\d{1,4}).*"
    match = re.match(pattern, objectId)
    if not match:
        print("objectId is not in the expected format: ^target-row-(\d{1,4})-source-groups-(\d{1,4})-(\d{1,4}).* returning with 204")
        return ("", 204)
    
    target_row = int(match.group(1))
    source_group_start = int(match.group(2))
    source_group_end = int(match.group(3))

    # Run checks on existance of target table
    bq_client = bigquery.Client(project=project_id)
    target_table_ref = bq_client.dataset(dataset_id).table(target_table) 
    try:
        bq_client.get_table(target_table_ref)  # Will raise NotFound if the table doesn't exist
        target_query = f"SELECT * FROM `{project_id}.{dataset_id}.{target_table}`"
        target_df = bq_client.query(target_query).to_dataframe()
        print(f"Job: {objectId}: Target table {target_table} exists. target_df created. Length is {target_df.shape[0]}. Ready to start work...")
    except:
        print(f"Job: {objectId}: Target table {target_table} does not exist (or isses with creating df from table). Returning with 204...")
        return ("",204)
    
    # Source table setup
    source_table_ref = bq_client.dataset(dataset_id).table(source_table) 
    try:
        bq_client.get_table(source_table_ref)  # Will raise NotFound if the table doesn't exist
        source_query = f"SELECT * FROM `{project_id}.{dataset_id}.{source_table}`"
        source_df = bq_client.query(source_query).to_dataframe()
        print(f"Job: {objectId}: Source table {source_table} exists. source_df created. Length is {source_df.shape[0]}. Ready to start work...")
    except:
            print(f"Job: {objectId}: Source table {source_table} does not exist (or isses with creating df from table). Returning with 204...")
            return ("",204)

    
    # Copy the object to the in process bucket and remove from jobs queue bucket
    in_progress_blob = queued_jobs_bucket.copy_blob(queued_blob, in_progress_jobs_bucket, objectId) #Copy
    print(f"Job {objectId}: copied job to in progress jobs bucket {in_progress_jobs_bucket.name}")
    queued_blob.delete()
    print(f"Job {objectId}: deleted job from queued jobs bucket {queued_jobs_bucket.name}. Starting work...")

    print(f"Job: {objectId}: target_row {target_row} source_group_start {source_group_start} source_group_end {source_group_end}. env vars: project_id={project_id}, dataset_id={dataset_id}, target_table={target_table}, mapped_table={mapped_table}, in_progress_jobs_bucket_name={in_progress_jobs_bucket_name}, completed_jobs_bucket_name={completed_jobs_bucket_name}, failed_jobs_bucket_name={failed_jobs_bucket_name}")

    model = GenerativeModel("gemini-pro")

    set_source_field_mapping_confidence_levels = generative_models.FunctionDeclaration(
    name="set_source_field_mapping_confidence_levels",
    description="""Sets the mapping confidence values for each source field for a given target field.

Here is a general example to help you understand how to use the set_source_field_mapping_confidences_tool correctly. This is only an example to show the source and target field structures.:

Assuming you had previously decided on the following mapping confidence levels (but it is important that you come up with your own values for mapping condifence level rather than specifically using these values):
a mapping confidence level of 2 for the field with Source_Unique_Ref=158
a mapping confidence level of 1 for the field with Source_Unique_Ref=159
a mapping confidence level of 1 for the field with Source_Unique_Ref=1290
a mapping confidence level of 1 for the field with Source_Unique_Ref=579
a mapping confidence level of 1 for the field with Source_Unique_Ref=638
a mapping confidence level of 1 for the field with Source_Unique_Ref=970
a mapping confidence level of 1 for the field with Source_Unique_Ref=3317
a mapping confidence level of 3 for the field with Source_Unique_Ref=160
a mapping confidence level of 1 for the field with Source_Unique_Ref=1910
a mapping confidence level of 5 for the field with Source_Unique_Ref=2280

Then this function would be used to set the mapping confidence levels for each of the source fields, where your input parameters would be
'mapping_confidence_level'=["2", "1", "1", "1", "1", "1", "1", "3", "1", "5"], 'Source_Unique_Ref': [158, 159, 1290, 579, 638, 970, 3317, 160, 1910, 2280]
And notice that the array index positions for each parameter align with each other to represent the mapping for a particular source field. This is very important.""",
    parameters={
        "type": "object",
        "properties": {
            "Source_Unique_Ref": {
                "type": "array",
                "description": "An array containing each of the Source_Unique_Ref values for the set of source fields to set a mapping confidence level for.",
                "items" : {
                    "type": "integer"
                },
                "example": [158, 159, 1290, 579, 638, 970, 3317, 160, 1910, 2280]
            },
            "mapping_confidence_level": {
                "type": "array",
                "description": "The mapping confidence level for the corresponding source field in the same index in the Source_Unique_Ref parameter. It is very important that the array indexes for mapping_confidence_level align to the Source_Unique_Ref so the mapping confidence levels are aligned to the correct source fields.",
                "items" : {
                    "type": "string"
                },
                "example": ["2", "1", "1", "1", "1", "1", "1", "3", "1", "5"]
            },
        },
        "required": ["Source_Unique_Ref", "mapping_confidence_level"]
    },
)

    set_source_field_mapping_confidence_levels_tool = generative_models.Tool(
        function_declarations=[set_source_field_mapping_confidence_levels]
    )

    # Prepare source field groups from job object 
    job_contents = in_progress_blob.download_as_string().decode('utf-8')
    job_contents_list = job_contents.split("\n\n")  # Split by double newlines
    
    unmapped_source_string_groups = []

    for job_content in job_contents_list:
        if "Row:" in job_content:
            unmapped_source_string_groups.append(job_content)

    # Prepare target field
    target_df_row = target_df.iloc[[target_row]]
    target_string_row = dataframe_to_string(target_df_row)

    df_list_for_upload = []
    succeeded_source_string_groups = []
    failed_source_string_groups = []

    for j, unmapped_source_string_group in enumerate(unmapped_source_string_groups):

        field_count = unmapped_source_string_group.count('Row:')

        prompt = f"""You are Data Engineer working for an insurance company. As part of a data migration project you need to assist with mapping fields in a source data schema fields in a target data schema.
The source and destination schemas are both complex and nested.
You will be shown 1 field in the target schema and multiple fields in the source schema.
The mappings will not be exactly one to one: Instead of providing a one-to-one mapping for a single source schema to a single destiation schema, your job is to provide a mapping confidence level for how well you think each of the fields for the source schemas you see will map to the field for the target schema.

The field from the target schema is described here:
{target_string_row}

The fields taken from the source schema are described here:
{unmapped_source_string_group}

Based on your knowledge of the insurance industry, pets, pet insurance, you will provide a mapping confidence level for how well each of the source fields map to the target field.
You must think very carefully about the mapping confidence level you apply for each source field, as it will be used in later process steps to implement the automated data migration pipelines, so any innacuracies lead to very costly errors.
The confidence level is a number between 1 and 5 where:
1 means there is a no chance that the fields could be a match
2 means there is a small chance that the fields colud be a match
3 means there is a good chance that the fields could be a match
4 means there is a very good chance that the fields could be a match
5 means there is a very very good chance that the fields could be a match

You should decide on a mapping confidence level for each of the source fields, then set the mapping confidence level for each field using and use the value for Source_Unique_Ref for each source field to reference it with its corresponding mapping confidence level.
Then YOU MUST USE the available function set_source_field_mapping_confidence_levels in the set_source_field_mapping_confidence_levels_tool to set your mappings confidence level for each of the source fields.
YOU MUST USE THIS FUNCTION."""
        
        if field_count == 0:
            (f"Job: {objectId}: source-group-{j+source_group_start}: field_count is {field_count}. Full object contents is {unmapped_source_string_group}. As no fields, skipping this group and adding to list of failed source groups")
            failed_source_string_groups.append({'row': (j+source_group_start), 'content': unmapped_source_string_group})
        else:
            set_mappings_retries = 0
            set_mappings_max_retries = 3
            set_mappings_success = False
            this_prompt = prompt
            while set_mappings_retries <= set_mappings_max_retries and not set_mappings_success:
                try:
                    model_response = model.generate_content(
                        this_prompt,
                        generation_config={"temperature": 0},
                        tools=[set_source_field_mapping_confidence_levels_tool],
                    )
                    if not model_response.candidates[0].content.parts[0].function_call:
                        this_prompt = this_prompt + """
    YOU MUST USE THIS FUNCTION."""
                        raise Exception("GEMINI DID NOT USE FUNCTION CALL")
                    else:
                        function_call_json = parse_function_call(model_response.candidates[0].content.parts[0].function_call)
                        attributes_dict = function_call_json["attributes"]
                        
                        con1 = len(attributes_dict['mapping_confidence_level']) != len(attributes_dict['Source_Unique_Ref'])
                        if (con1):
                            raise Exception(f"GEMINI FUNCTION RESPONSE OBJECTS ARE NOT OF EQUAL LENGTH: fields:{field_count} mappings:{len(attributes_dict['mapping_confidence_level'])} rows:{len(attributes_dict['Source_Unique_Ref'])}")
                        
                        con2 = len(attributes_dict['mapping_confidence_level']) != field_count
                        if con2:
                            raise Exception(f"NUMBER OF FIELDS MAPPED BY GEMINI IS NOT EQUAL TO NUMBER OF INPUT FIELDS. fields:{field_count} mappings:{len(attributes_dict['mapping_confidence_level'])} rows:{len(attributes_dict['Source_Unique_Ref'])}")

                        for l, Source_Unique_Ref in enumerate(attributes_dict['Source_Unique_Ref']):
                            source_df_row = source_df[source_df['Source_Unique_Ref']==int(Source_Unique_Ref)]
                            confidence_level = attributes_dict['mapping_confidence_level'][l]
                            mapping_output = merge_dataframes_and_string(target_df_row, source_df_row, confidence_level)
                            df_list_for_upload.append(mapping_output)

                        succeeded_source_string_groups.append({'name': f"target-row-{target_row}-source-groups-{j+source_group_start}-{j+source_group_start}", 'content': unmapped_source_string_group})
                        print(f"Job: {objectId}: source-group-{j+source_group_start}: Sucessful mapping response received from Gemini. Prepared the mapping as a df ready for upload to bigquery...")
                        set_mappings_success = True

                except Exception as error:
                    if set_mappings_retries < set_mappings_max_retries:
                        print(f"ERROR on job {objectId}, source-group-{j+source_group_start}  when calling Gemini: (retry attempt {set_mappings_retries}/{set_mappings_max_retries}): {error}. Retrying in {1+(set_mappings_retries*set_mappings_retries)} seconds...")
                        time.sleep(1+(set_mappings_retries*set_mappings_retries))  # Non linear backoff
                    else:
                        print(f"ERROR on job {objectId}, source-group-{j+source_group_start} when calling Gemini: {error}. Out of retry attempts. Appending failed group to failed List... ")
                        failed_source_string_groups.append({'row': j+source_group_start, 'content': unmapped_source_string_group})
                    set_mappings_retries += 1

    print(f"Job {objectId}: GEMINI ITERATION COMPLETE. Iteration contained {len(df_list_for_upload)} mapped source fields across the {len(succeeded_source_string_groups)} successful groups, with {len(failed_source_string_groups)} failed groups")
    
    upload_retries = 0
    upload_max_retries = 3
    upload_success = False

    #Copy any individual failed source string groups to failed bucket.    
    if len(failed_source_string_groups) == 0:
        print(f"job {objectId}: 0 failed source string groups to upload to failed jobs bucket.")
    else:    
        failed_source_string_group_object_content = ""
        failed_source_string_group_object_name_suffix = ""
        for failed_source_string_group in failed_source_string_groups:
            failed_source_string_group_object_content += f"{failed_source_string_group['content']}\n\n"
            failed_source_string_group_object_name_suffix += f"{failed_source_string_group['row']},"
        
        failed_blob_prefix = ""
        if ',' in objectId:
            failed_blob_prefix = objectId.rsplit('-', 1)[0]
        else:
            failed_blob_prefix = objectId
            
        new_failed_blob_name = f"{failed_blob_prefix}-{failed_source_string_group_object_name_suffix}"
        print(f"Job {objectId}: adding {len(failed_source_string_groups)} failed groups to failed bucket {failed_jobs_bucket_name} with name {new_failed_blob_name}")
        
        new_failed_blob = failed_jobs_bucket.blob(new_failed_blob_name)
        new_failed_blob.upload_from_string(failed_source_string_group_object_content)
    
    if len(df_list_for_upload) == 0:
        print(f"job {objectId}: 0 successfully mapped source fields to upload.")
    else:
        while upload_retries <= upload_max_retries and not upload_success:
            try:            
                df_for_upload = pd.concat(df_list_for_upload)
                
                dataset_ref = bq_client.dataset(dataset_id)
                job_config = bigquery.LoadJobConfig(
                    schema=[],
                    write_disposition="WRITE_APPEND",
                    schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
                )
                
                if upload_retries < upload_max_retries:
                    print(f"Job {objectId}: BQ UPLOAD STARTING to table {mapped_table}...") 
                    table_ref = dataset_ref.table(mapped_table)
                    bq_job = bq_client.load_table_from_dataframe(df_for_upload, table_ref, job_config=job_config)  
                    bq_job.result()
                    print(f"Job {objectId}: Job was successfully uploaded to BigQuery. Moving Job status to completed and moving any individual failed source groups to failed bucket")
                else:
                    print(f"Job {objectId}: CSV UPLOAD STARTING to bucket {bq_upload_queue_bucket_name}") 
                    csv_blob = bq_upload_queue_bucket.blob(f"{objectId}.csv")
                    csv_blob.upload_from_string(df_for_upload.to_csv(index=False), 'text/csv')
                    print(f"Job {objectId}: Job was successfully uploaded to Bucket {bq_upload_queue_bucket_name} for later batch processing. Moving Job status to completed and moving any individual failed source groups to failed bucket")
                upload_success = True
            except Exception as error:
                if upload_retries <= upload_max_retries:
                    print(f"ERROR on job {objectId} when uploading data: (retry attempt {upload_retries}/{upload_max_retries}): {error}. Retrying in {1+(upload_retries*upload_retries)} seconds...")
                    time.sleep(1+(upload_retries*upload_retries))
                else:
                    print(f"ERROR on job {objectId} when uploading data. {error}. Out of retry attempts.")
                    upload_success = False
            upload_retries += 1
    
    if upload_success:   
        #Copy job to successful bucket
        print(f"Job {objectId}: moving job from in-progress bucket {in_progress_jobs_bucket.name} to completed bucket {completed_jobs_bucket_name}...")                
        completed_blob = in_progress_jobs_bucket.copy_blob(in_progress_blob, completed_jobs_bucket, objectId) #Copy
        print(f"Job {objectId}: copied job to completed jobs bucket {completed_jobs_bucket.name}")
    else:
        #Copy job to failed bucket              
        failed_blob = in_progress_jobs_bucket.copy_blob(in_progress_blob, failed_jobs_bucket, objectId) #Copy
        print(f"Job {objectId}: copied job to failed jobs bucket {failed_jobs_bucket.name}")
    
    #Remove job from in progress bucket
    in_progress_blob.delete()
    print(f"Job {objectId}: deleted job from in progress jobs bucket {in_progress_jobs_bucket.name}.")
    print(f"Job {objectId}: COMPLETED JOB")
    return ("", 204)

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

def parse_function_call(function_call):
    """Parses a FunctionCall object, adds a description, and returns a JSON-compatible dictionary.

    Args:
        function_call: The FunctionCall object to parse.

    Returns:
        A dictionary containing the function name, attributes, and description.
    """

    result = {
        "function_name": function_call.name,
        "attributes": {},
    }
    for key, value in function_call.args.items():
        result["attributes"][key] = value

    return result

def merge_dataframes_and_string(target_df_row, source_df_row, confidence_level):
    # Reset index to ensure proper concatenation
    target_df_row = target_df_row.reset_index(drop=True)
    source_df_row = source_df_row.reset_index(drop=True)

    # Concatenate the two dataframes horizontally
    merged_df = pd.concat([target_df_row, source_df_row], axis=1)

    # Create a new dataframe with the string variable
    confidence_df = pd.DataFrame({'Confidence_Levels': [confidence_level]})

    # Concatenate the merged dataframe with the confidence dataframe vertically
    final_df = pd.concat([merged_df, confidence_df], axis=1)

    return final_df




######################
# BELOW IS FOR RUN 1 #
######################

# prompt = f"""You are senior Data Engineer working for an insurance company. As part of a data migration project you need to set the confidence mapping values for how well a group of source data schema fields map to a a target data schema.
# The source and destination schemas are both complex and nested. You will be shown 1 field in the target schema and multiple fields in the source schema.
# The mappings will not be exactly one to one: Instead of providing a one-to-one mapping for a single source schema to a single destiation schema, your job is to provide a mapping confidence level for how well you think each of the fields for the source schema you see will map to the field for the target schema.

# The field from the target schema is described here:
# {target_string_row}

# The fields taken from the source schema are described here:
# {unmapped_source_string_group}

# Based on your knowledge of the insurance industry, pets, pet insurance, and data structures for complex and legacy IT data systems, you will provide a mapping confidence level for how well each of the source fields map to the target field.
# You should look at each source field carefully and decide on a mapping confidence level to the best of your availability, and use the number range explained here to help you show you level of confidence:
# The mapping confidence level is a number between 1 and 5 where:
# 1 means there is a very very small chance that the fields could be a match
# 2 means there is a small chance that the fields colud be a match
# 3 means there is a medium chance that the fields could be a match
# 4 means there is a good chance that the fields could be a match
# 5 means there is a very good chance that the fields could be a match

# For example: assuming the target field was...
# Column Names: Unique_Ref, Tranche, Level_1, Level_2, Level_3, Level_4, Complex_Type, Attribute, Description, Mandatory__, Data_Type, Accepted_Values, Validation, Drop_Down_Metaval, Target_Unique_Ref
# Row: 60, CLIENT, Client, emailAddress, n/a, n/a, emailAddress, email, The email address, Optional, string (100), None, None, 48

# ...and you were shown 10 source fields like this...
# Column Names: SchemaName, TableName, Column_Name, Data_type, Max_Length, precision, scale, is_nullable, Source_Unique_Ref
# Row: dbo, bacs_premium_refund_batch, BacsRefundAccountFromId, int, 4, 10, 0, 0, 158
# Row: dbo, bacs_premium_refund_batch, payee_count, int, 4, 10, 0, 0, 159
# Row: dbo, bacs_premium_refund_batch, verified_by_systuser_id, int, 4, 10, 0, 1, 1290
# Row: dbo, bacs_premium_refund_batch, batch_no, char, 15, 0, 0, 0, 579
# Row: dbo, bacs_premium_refund_batch, total_amount, money, 8, 19, 4, 0, 638
# Row: dbo, bacs_premium_refund_batch, datetimestamp, datetime, 8, 23, 3, 0, 970
# Row: dbo, bacs_premium_refund_batch, verified_datetimestamp, datetime, 8, 23, 3, 1, 3317
# Row: dbo, bacs_premium_refund_notifier, id, int, 4, 10, 0, 0, 160
# Row: dbo, bacs_premium_refund_notifier, item_threshold, money, 8, 19, 4, 1, 1910
# Row: dbo, bacs_premium_refund_notifier, email_address, varchar, 255, 0, 0, 1, 2280

# ...You would first estimate a mapping confidence level for each of the fields, for example you may decide the following:
# a mapping confidence level of 2 for the field with Source_Unique_Ref=158, because you think there is a very small chance that this source field would map to the target row
# a mapping confidence level of 1 for the field with Source_Unique_Ref=159, because you think there is a very very small chance that this source field would map to the target row
# a mapping confidence level of 1 for the field with Source_Unique_Ref=1290, because you think there is a very very small chance that this source field would map to the target row
# a mapping confidence level of 1 for the field with Source_Unique_Ref=579, because you think there is a very very small chance that this source field would map to the target row
# a mapping confidence level of 1 for the field with Source_Unique_Ref=638, because you think there is a very very small chance that this source field would map to the target row
# a mapping confidence level of 1 for the field with Source_Unique_Ref=970, because you think there is a very very small chance that this source field would map to the target row
# a mapping confidence level of 1 for the field with Source_Unique_Ref=3317, because you think there is a very very small chance that this source field would map to the target row
# a mapping confidence level of 3 for the field with Source_Unique_Ref=160, because you think there is a medium chance that this source field would map to the target row
# a mapping confidence level of 1 for the field with Source_Unique_Ref=1910, because you think there is a very very small chance that this source field would map to the target row
# a mapping confidence level of 5 for the field with Source_Unique_Ref=2280, because you think there is a very good chance that this source field would map to the target row

# (but it is important that you come up with your own values for the mapping condifence level rather than specifically using these values.)

# Once you have decided on a mapping confidence level for each source field, only then should you set the mapping confidence levels for each source field using the function set_source_field_mapping_confidence_levels in the set_source_field_mapping_confidence_levels_tool. YOU MUST USE THIS FUNCTION once you have decided on the mapping confidence level values.

# In summary, you are being asked to do two things:
# 1) review the source fields and decide on a mapping confidence level for each field
# 2) then set that mapping confidence levels for the source fields using the function set_source_field_mapping_confidence_levels in the set_source_field_mapping_confidence_levels_tool."""



######################
# BELOW IS FOR RUN 2 #
######################

# set_source_field_mapping_confidence_levels = generative_models.FunctionDeclaration(
#     name="set_source_field_mapping_confidence_levels",
#     description="""Sets the mapping confidence values for each source field for a given target field.

# Here is a general example to help you understand how to use the set_source_field_mapping_confidences_tool correctly. This is only an example to show the source and target field structures.:

# Assuming you had previously decided on the following mapping confidence levels (but it is important that you come up with your own values for mapping condifence level rather than specifically using these values):
# a mapping confidence level of 2 for the field with Source_Unique_Ref=158
# a mapping confidence level of 1 for the field with Source_Unique_Ref=159
# a mapping confidence level of 1 for the field with Source_Unique_Ref=1290
# a mapping confidence level of 1 for the field with Source_Unique_Ref=579
# a mapping confidence level of 1 for the field with Source_Unique_Ref=638
# a mapping confidence level of 1 for the field with Source_Unique_Ref=970
# a mapping confidence level of 1 for the field with Source_Unique_Ref=3317
# a mapping confidence level of 3 for the field with Source_Unique_Ref=160
# a mapping confidence level of 1 for the field with Source_Unique_Ref=1910
# a mapping confidence level of 5 for the field with Source_Unique_Ref=2280

# Then this function would be used to set the mapping confidence levels for each of the source fields, where your input parameters would be
# 'mapping_confidence_level'=["2", "1", "1", "1", "1", "1", "1", "3", "1", "5"], 'Source_Unique_Ref': [158, 159, 1290, 579, 638, 970, 3317, 160, 1910, 2280]
# And notice that the array index positions for each parameter align with each other to represent the mapping for a particular source field. This is very important.""",
#     parameters={
#         "type": "object",
#         "properties": {
#             "Source_Unique_Ref": {
#                 "type": "array",
#                 "description": "An array containing each of the Source_Unique_Ref values for the set of source fields to set a mapping confidence level for.",
#                 "items" : {
#                     "type": "integer"
#                 },
#                 "example": [158, 159, 1290, 579, 638, 970, 3317, 160, 1910, 2280]
#             },
#             "mapping_confidence_level": {
#                 "type": "array",
#                 "description": "The mapping confidence level for the corresponding source field in the same index in the Source_Unique_Ref parameter. It is very important that the array indexes for mapping_confidence_level align to the Source_Unique_Ref so the mapping confidence levels are aligned to the correct source fields.",
#                 "items" : {
#                     "type": "string"
#                 },
#                 "example": ["2", "1", "1", "1", "1", "1", "1", "3", "1", "5"]
#             },
#         },
#         "required": ["Source_Unique_Ref", "mapping_confidence_level"]
#     },
# )


#         prompt = f"""You are Data Engineer working for an insurance company. As part of a data migration project you need to assist with mapping fields in a source data schema fields in a target data schema.
# The source and destination schemas are both complex and nested.
# You will be shown 1 field in the target schema and multiple fields in the source schema.
# The mappings will not be exactly one to one: Instead of providing a one-to-one mapping for a single source schema to a single destiation schema, your job is to provide a mapping confidence level for how well you think each of the fields for the source schemas you see will map to the field for the target schema.

# The field from the target schema is described here:
# {target_string_row}

# The fields taken from the source schema are described here:
# {unmapped_source_string_group}

# Based on your knowledge of the insurance industry, pets, pet insurance, you will provide a mapping confidence level for how well each of the source fields map to the target field.
# The confidence level is a number between 1 and 5 where:
# 1 means there is a very very small chance that the fields could be a match
# 2 means there is a small chance that the fields colud be a match
# 3 means there is a medium chance that the fields could be a match
# 4 means there is a good chance that the fields could be a match
# 5 means there is a very good chance that the fields could be a match

# You should decide on a mapping confidence level for each of the source fields, then set the mapping confidence level for each field using and use the value for Source_Unique_Ref for each source field to reference it with its corresponding mapping confidence level.
# Then YOU MUST USE the available function set_source_field_mapping_confidence_levels in the set_source_field_mapping_confidence_levels_tool to set your mappings confidence level for each of the source fields.
# YOU MUST USE THIS FUNCTION."""