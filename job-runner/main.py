import os
from google.cloud import bigquery
from google.cloud import storage
import pandas as pd
from vertexai.preview import generative_models
from vertexai.preview.generative_models import GenerativeModel
import re
import time
from proto.marshal.collections import repeated
from proto.marshal.collections import maps

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
a mapping confidence level of 2 for the field with source_field_unique_ref=158
a mapping confidence level of 1 for the field with source_field_unique_ref=159
a mapping confidence level of 1 for the field with source_field_unique_ref=1290
a mapping confidence level of 1 for the field with source_field_unique_ref=579
a mapping confidence level of 1 for the field with source_field_unique_ref=638
a mapping confidence level of 1 for the field with source_field_unique_ref=970
a mapping confidence level of 1 for the field with source_field_unique_ref=3317
a mapping confidence level of 3 for the field with source_field_unique_ref=160
a mapping confidence level of 1 for the field with source_field_unique_ref=1910
a mapping confidence level of 5 for the field with source_field_unique_ref=2280

Then this function would be used to set the mapping confidence levels for each of the source fields, where your input parameter source_field_mapping_confidences would be:
source_field_mapping_confidences = [
    {'source_field_unique_ref':158,'mapping_confidence_level':'2'},
    {'source_field_unique_ref':159,'mapping_confidence_level':'2'},
    {'source_field_unique_ref':1290,'mapping_confidence_level':'1'},
    {'source_field_unique_ref':579,'mapping_confidence_level':'1'},
    {'source_field_unique_ref':638,'mapping_confidence_level':'1'},
    {'source_field_unique_ref':970,'mapping_confidence_level':'1'},
    {'source_field_unique_ref':3317,'mapping_confidence_level':'1'},
    {'source_field_unique_ref':160,'mapping_confidence_level':'3'},
    {'source_field_unique_ref':1910,'mapping_confidence_level':'1'},
    {'source_field_unique_ref':2280,'mapping_confidence_level':'5'}
]""",

        parameters={
            "type": "object",
            "properties": {
                "source_field_mapping_confidences": {
                    "type": "array",
                    "description": "A List of objects where each object in the list contains the source field's source_field_unique_ref, the mapping_confidence_level for that source field and the reason for applying that mapping_confidence_level.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_field_unique_ref": {
                                "type": "integer",
                                "description": "The reference ID for the source field."
                            },
                            "mapping_confidence_level": {
                                "type": "string",
                                "enum": ["1", "2", "3", "4", "5"],
                                "description": "The confidence level for the mapping (an integer between 1 and 5)."
                            },
                            "mapping_confidence_level_reason": {
                                "type": "string",
                                "description": "The reason why the source field should have this mapping confidence level value"
                            }
                        },
                        "required": ["source_field_unique_ref", "mapping_confidence_level", "mapping_confidence_level_reason"]
                    }
                },
            },
            "required": ["source_field_mapping_confidences"],
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
        if "source_field:" in job_content:
            unmapped_source_string_groups.append(job_content)

    # Prepare target field
    target_df_row = target_df.iloc[[target_row]]
    target_string_row = dataframe_to_custom_target_string(target_df_row)

    df_list_for_upload = []
    succeeded_source_string_groups = []
    failed_source_string_groups = []

    for j, unmapped_source_string_group in enumerate(unmapped_source_string_groups):

        field_count = unmapped_source_string_group.count('source_field:')

        prompt = f"""You are Data Engineer working for an insurance company. As part of a data migration project you need to assist with mapping fields in a source data schema fields in a target data schema. Your job is to provide a mapping confidence level for how well you think each of the fields for the source schemas you see will map to the field for the target schema.
This will be used as part of an automated data migration process so your mapping confidence level describes how confident you are that the data in the source field could be directly loaded into this target field without modification and it would make logical sense and contextual sense for the data to be put into that target field.

Here is some information about the source fields:
The fields from the source schema are also custom complex nested objects. They will have two levels of nesting, for example: Contact.Preference.Method
Similar to the target field, each layer of nesting of the source fields is an important consideration for whether these source fields will map well to the target field.
Similar to the target field, you may also be given the data types of the source fields. These are the standard types (e.g. string, int, boolean, dateTime, etc.) of the lowest level of nesting for each source field. These are also an important consideration for the mapping.

Here is some information about the target field:
The field from the target schema is a custom complex nested object. It will be at a minimum one level of nesting, for example {target_df_row['Target_Level_1'].iloc[0]}.id, and at a maximum 4 layers of nesting, for example {target_df_row['Target_Level_1'].iloc[0]}.namedPerson.namedDriver.email.emailAddress.
Each layer of nesting is a vary important consideration for whether the source fields will map well to this target field, for example, consider the target fields Client.person.dateOfBirth and Policy.namedPerson.namedPerson (Motor).dateOfBirth. Although these have the same value for their lowest level of nesting in the field type (dateOfBirth), as first is referencing the date of birth of the client of the policy because its top level object is Client, and the second is referring to a named driver thats been added to a motor policy (which is not necessarily the same person), because its top level object is Policy. This example is to show you that its VERY important that you consider the ENTIRE nested structure of the target field to decide on the mapping confidence level.
In addition, you may also be given the data type of the target field. This is the standard type (e.g. string, int, boolean, dateTime, etc.) of the lowest level of nesting for the field. This is also an important consideration for the mapping.
In addition, there may also be a description of the target field. This is not present in all cases, but if it is present then please use this to help you better understand what this target field is referring to.
You may also get additional information such as the possible accepted values for this target field, any validation logic for this field, or other information. Please use this information when making your mapping decision. 

You are being shown shown multiple fields in the source schema which are here:
{unmapped_source_string_group}

And one field from the target schema which is here:
{target_string_row}

Here is some information about how you should go about this job:
Based on your knowledge of the insurance industry, home insurance, motor insurance, pets, pet insurance, and other related insurance industry concepts and data structures, you will provide a mapping confidence level for each of the source fields that describes how well you think that source field would map to the target field.
You must think very carefully about the mapping confidence level you apply for each source field, as it will be used in later process steps to implement the automated data migration pipelines, so any inaccuracies lead to very costly errors.
Remember that you need to consider EVERY NESTED LAYER of both the target field and the source fields to comprehend what kind of information they each represent, and therefore whether they are a good or bad mapping.
As the value of the top level of the nested object of the target field is {target_df_row['Target_Level_1'].iloc[0]}, this means that the target field is only relevant to 
{"the client that has taken out a policy." if target_df_row['Target_Level_1'].iloc[0] == 'Client' else ""}{"a household insurance or home insurance policy." if target_df_row['Target_Level_1'].iloc[0] == 'Household Policy' else ""}{"a motor insurance policy, or Motorcar policy data or car insurance data." if target_df_row['Target_Level_1'].iloc[0] == 'Motor Policy' else ""}{"a pet insurance policy, or the pet that is being insured against in the pet insurance policy." if target_df_row['Target_Level_1'].iloc[0] == 'Pet' else ""}{"a Policy that has been created or is being created by the client." if target_df_row['Target_Level_1'].iloc[0] == 'Policy' else ""}
So you should only give high confidence mapping levels to source fields that also refer to {target_df_row['Target_Level_1'].iloc[0]} data. If you think the source field is not referring specifically to {target_df_row['Target_Level_1'].iloc[0]} data, you should not give a high mapping confidence level.
You must also give a detailed reason for why you decided on that mapping confidence level.

The mapping confidence level you will apply must be a number between 1 and 5 where:
1 means there is a no chance that the source field matches the target field
2 means there is a small chance the source field matches the target field
3 means there is a good chance the source field matches the target field
4 means there is a very good chance the source field matches the target field
5 means there is a very very good chance the source field matches the target field

You should decide on a mapping confidence level for each of the source fields, then set the mapping confidence level for each field using and use the value for source_field_unique_ref for each source field to reference it with its corresponding mapping confidence level as well as the reason for why you gave that confidence level.
Then YOU MUST USE the available function set_source_field_mapping_confidence_levels in the set_source_field_mapping_confidence_levels_tool to set your mappings confidence level for each of the source fields.
YOU MUST USE THIS FUNCTION."""
        
        if field_count == 0:
            print(f"Job: {objectId}: source-group-{j+source_group_start}: field_count is {field_count}. Full object contents is {unmapped_source_string_group}. As no fields, skipping this group and adding to list of failed source groups")
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
                        this_prompt = this_prompt + "\nYOU MUST USE THIS FUNCTION."
                        raise Exception("GEMINI DID NOT USE FUNCTION CALL")
                    else:
                        function_call_json = parse_function_call(model_response.candidates[0].content.parts[0].function_call)
                        attributes = function_call_json["attributes"]
                        
                        if len(attributes['source_field_mapping_confidences']) != field_count:
                            raise Exception(f"NUMBER OF FIELDS MAPPED BY GEMINI IS NOT EQUAL TO NUMBER OF INPUT FIELDS. fields:{field_count} mappings:{len(attributes['source_field_mapping_confidences'])}")

                        for l, attribute in enumerate(attributes['source_field_mapping_confidences']):
                            mapping_dict = recurse_proto_marshal_to_dict(attribute)
                            
                            Source_Unique_Ref_int = int(mapping_dict['source_field_unique_ref'])
                            source_df_row = source_df[source_df['Source_Unique_Ref']==Source_Unique_Ref_int]

                            mapping_confidence_level_int = int(mapping_dict['mapping_confidence_level'])
                            mapping_confidence_level_reason = mapping_dict['mapping_confidence_level_reason']
                            
                            mapping_output = merge_dataframes_and_string(target_df_row, source_df_row, mapping_confidence_level_int, mapping_confidence_level_reason)
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
        #Copy job to completed bucket             
        completed_blob = in_progress_jobs_bucket.copy_blob(in_progress_blob, completed_jobs_bucket, objectId) #Copy
        print(f"Job {objectId}: copied job from in-progress bucket {in_progress_jobs_bucket.name} to completed jobs bucket {completed_jobs_bucket.name}")
    else:
        while upload_retries <= upload_max_retries and not upload_success:
            try:            
                df_for_upload = pd.concat(df_list_for_upload)
                
                # dataset_ref = bq_client.dataset(dataset_id)
                # job_config = bigquery.LoadJobConfig(
                #     schema=[],
                #     write_disposition="WRITE_APPEND",
                #     schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]
                # )
                
                # if upload_retries < upload_max_retries:
                #     print(f"Job {objectId}: BQ UPLOAD STARTING to table {mapped_table}...") 
                #     table_ref = dataset_ref.table(mapped_table)
                #     bq_job = bq_client.load_table_from_dataframe(df_for_upload, table_ref, job_config=job_config)  
                #     bq_job.result()
                #     print(f"Job {objectId}: Job was successfully uploaded to BigQuery. Moving Job status to completed and moving any individual failed source groups to failed bucket")
                # else:
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
            #Copy job to completed bucket             
            completed_blob = in_progress_jobs_bucket.copy_blob(in_progress_blob, completed_jobs_bucket, objectId) #Copy
            print(f"Job {objectId}: copied job from in-progress bucket {in_progress_jobs_bucket.name} to completed jobs bucket {completed_jobs_bucket.name}")
        else:
            #Copy job to failed bucket              
            failed_blob = in_progress_jobs_bucket.copy_blob(in_progress_blob, failed_jobs_bucket, objectId) #Copy
            print(f"Job {objectId}: copied job from in-progress bucket {in_progress_jobs_bucket.name} to failed jobs bucket {failed_jobs_bucket.name}")
    
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

def dataframe_to_custom_target_string(df):

    output = ""  # Header with column names

    for _, row in df.iterrows():
        row_string = f"target_field: {row['Target_Level_1']}"
        if row['Target_Level_2'] != 'n/a':
            row_string += f".{row['Target_Level_2']}"
        if row['Target_Level_3'] != 'n/a':
            row_string += f".{row['Target_Level_3']}"
        if row['Target_Level_4'] != 'n/a':
            row_string += f".{row['Target_Level_4']}"
        row_string += f".{row['Target_Attribute']}; "
        if row['Target_Data_Type'] != '' and row['Target_Data_Type']:
            row_string += f"data_type: {row['Target_Data_Type']}; "
        if row['Target_Description'] != '' and row['Target_Description']:
            row_string += f"target_field_description: {row['Target_Description']}; "
        row_string += f"target_field_unique_ref: {row['Target_Unique_Ref']}"

        output += f"{row_string}\n"

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

def merge_dataframes_and_string(target_df_row, source_df_row, confidence_level, mapping_confidence_level_reason):
    # Reset index to ensure proper concatenation
    target_df_row = target_df_row.reset_index(drop=True)
    source_df_row = source_df_row.reset_index(drop=True)

    # Concatenate the two dataframes horizontally
    merged_df = pd.concat([target_df_row, source_df_row], axis=1)

    # Create a new dataframe with the string variable
    confidence_df = pd.DataFrame({'Confidence_Levels': [confidence_level]})

    # Create a new dataframe with the string variable for mapping_confidence_level_reason
    mapping_confidence_level_reason_df = pd.DataFrame({'Confidence_Levels_Reason': [mapping_confidence_level_reason]})

    # Concatenate the merged dataframe with the confidence dataframe vertically
    final_df = pd.concat([merged_df, confidence_df, mapping_confidence_level_reason_df], axis=1)

    return final_df

def recurse_proto_repeated_composite(repeated_object):
    repeated_list = []
    for item in repeated_object:
        if isinstance(item, repeated.RepeatedComposite):
            item = recurse_proto_repeated_composite(item)
            repeated_list.append(item)
        elif isinstance(item, maps.MapComposite):
            item = recurse_proto_marshal_to_dict(item)
            repeated_list.append(item)
        else:
            repeated_list.append(item)

    return repeated_list

def recurse_proto_marshal_to_dict(marshal_object):
    new_dict = {}
    for k, v in marshal_object.items():
      if not v:
        continue
      elif isinstance(v, maps.MapComposite):
          v = recurse_proto_marshal_to_dict(v)
      elif isinstance(v, repeated.RepeatedComposite):
          v = recurse_proto_repeated_composite(v)
      new_dict[k] = v

    return new_dict