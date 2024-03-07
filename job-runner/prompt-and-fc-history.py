

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

######################
# BELOW IS FOR RUN 3 #
######################


#         prompt = f"""You are Data Engineer working for an insurance company. As part of a data migration project you need to assist with mapping fields in a source data schema fields in a target data schema.
# The source and destination schemas are both complex and nested.
# You will be shown 1 field in the target schema and multiple fields in the source schema.
# The mappings will not be exactly one to one: Instead of providing a one-to-one mapping for a single source schema to a single destiation schema, your job is to provide a mapping confidence level for how well you think each of the fields for the source schemas you see will map to the field for the target schema.

# The field from the target schema is described here:
# {target_string_row}

# The fields taken from the source schema are described here:
# {unmapped_source_string_group}

# Based on your knowledge of the insurance industry, pets, pet insurance, you will provide a mapping confidence level for how well each of the source fields map to the target field.
# You must think very carefully about the mapping confidence level you apply for each source field, as it will be used in later process steps to implement the automated data migration pipelines, so any innacuracies lead to very costly errors.
# The confidence level is a number between 1 and 5 where:
# 1 means there is a no chance that the fields could be a match
# 2 means there is a small chance that the fields colud be a match
# 3 means there is a good chance that the fields could be a match
# 4 means there is a very good chance that the fields could be a match
# 5 means there is a very very good chance that the fields could be a match

# You should decide on a mapping confidence level for each of the source fields, then set the mapping confidence level for each field using and use the value for Source_Unique_Ref for each source field to reference it with its corresponding mapping confidence level.
# Then YOU MUST USE the available function set_source_field_mapping_confidence_levels in the set_source_field_mapping_confidence_levels_tool to set your mappings confidence level for each of the source fields.
# YOU MUST USE THIS FUNCTION."""

#     set_source_field_mapping_confidence_levels = generative_models.FunctionDeclaration(
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


######################
# BELOW IS FOR RUN 4 #
######################

#         prompt = f"""You are Data Engineer working for an insurance company. As part of a data migration project you need to assist with mapping fields in a source data schema fields in a target data schema.
# The source and destination schemas are both complex and nested.
# You will be shown 1 field in the target schema and multiple fields in the source schema.
# The mappings will not be exactly one to one: Instead of providing a one-to-one mapping for a single source schema to a single destiation schema, your job is to provide a mapping confidence level for how well you think each of the fields for the source schemas you see will map to the field for the target schema.

# The field from the target schema is described here:
# {target_string_row}

# The fields taken from the source schema are described here:
# {unmapped_source_string_group}

# Based on your knowledge of the insurance industry, pets, pet insurance, you will provide a mapping confidence level for how well each of the source fields map to the target field.
# You must think very carefully about the mapping confidence level you apply for each source field, as it will be used in later process steps to implement the automated data migration pipelines, so any innacuracies lead to very costly errors.
# The confidence level is a number between 1 and 5 where:
# 1 means there is a no chance that the fields could be a match
# 2 means there is a small chance that the fields colud be a match
# 3 means there is a good chance that the fields could be a match
# 4 means there is a very good chance that the fields could be a match
# 5 means there is a very very good chance that the fields could be a match

# You should decide on a mapping confidence level for each of the source fields, then set the mapping confidence level for each field using and use the value for Source_Unique_Ref for each source field to reference it with its corresponding mapping confidence level.
# Then YOU MUST USE the available function set_source_field_mapping_confidence_levels in the set_source_field_mapping_confidence_levels_tool to set your mappings confidence level for each of the source fields.
# YOU MUST USE THIS FUNCTION."""



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

# Then this function would be used to set the mapping confidence levels for each of the source fields, where your input parameter source_field_mapping_confidences would be:
# source_field_mapping_confidences = [
#     {'Source_Unique_Ref':158,'mapping_confidence_level':'2'},
#     {'Source_Unique_Ref':159,'mapping_confidence_level':'2'},
#     {'Source_Unique_Ref':1290,'mapping_confidence_level':'1'},
#     {'Source_Unique_Ref':579,'mapping_confidence_level':'1'},
#     {'Source_Unique_Ref':638,'mapping_confidence_level':'1'},
#     {'Source_Unique_Ref':970,'mapping_confidence_level':'1'},
#     {'Source_Unique_Ref':3317,'mapping_confidence_level':'1'},
#     {'Source_Unique_Ref':160,'mapping_confidence_level':'3'},
#     {'Source_Unique_Ref':1910,'mapping_confidence_level':'1'},
#     {'Source_Unique_Ref':2280,'mapping_confidence_level':'5'}
# ]""",

#     parameters={
#         "type": "object",
#         "properties": {
#             "source_field_mapping_confidences": {
#                 "type": "array",
#                 "description": "A List of objects where each object in the list contains the source field's Source_Unique_Ref and the mapping_confidence_level for that source field.",
#                 "items": {
#                     "type": "object",
#                     "properties": {
#                         "Source_Unique_Ref": {
#                             "type": "integer",
#                             "description": "The reference ID for the source field."
#                         },
#                         "mapping_confidence_level": {
#                             "type": "string",
#                             "enum": ["1", "2", "3", "4", "5"],
#                             "description": "The confidence level for the mapping (an integer between 1 and 5)."
#                         }
#                     },
#                     "required": ["Source_Unique_Ref", "mapping_confidence_level"]
#                 }
#             },
#         },
#         "required": ["source_field_mapping_confidences"],
#     },
# )


######################
# BELOW IS FOR RUN 5 #
######################

#         prompt = f"""You are Data Engineer working for an insurance company. As part of a data migration project you need to assist with mapping fields in a source data schema fields in a target data schema. Your job is to provide a mapping confidence level for how well you think each of the fields for the source schemas you see will map to the field for the target schema.

# You will be shown 1 field in the target schema and multiple fields in the source schema. 

# Here is some information about the target field:
# The field from the target schema is a custom complex nested object. It will be at a minimum one level of nesting, for example Client.branch, and at a maximum 4 layers of nesting, for example Policy.namedPerson.namedDriver.conviction.convictionDate
# The values of the top level of the nested object will be from the following values: [Client, Household Policy, Motor Policy, Pet, Policy], which will define the main classification of what this target field is relevant to:
# - Client = the target field is relevant only to the client that has taken out a policy
# - Household Policy = the target field is relevant only to a household insurance or home insurance policy
# - Motor Policy = the target field is relevant only to a motor insurance policy
# - Pet = The target field is relevant to either a pet insurance policy, or possibly the pet that is being insured against in the pet insurance policy.
# - Policy = The target field is relevant to a Policy that has been created or is being created by the client.
# Each layer of nesting is an important consideration for whether the source fields will map well to this target field, for example, consider the target fields Client.person.dateOfBirth and Policy.namedPerson.namedPerson (Motor).dateOfBirth. Although these have the same value for their lowest level of nesting in the field type (dateOfBirth), as first is referencing the date of birth of the client of the policy because it’s top level object is Client, and the second is referring to a named driver that’s been added to a  motor policy (which is not necessarily the same person), because it’s top level object is Policy. This example is to show you that it’s important that you consider the entire nested structure of the target field to decide on the mapping confidence level.
# In addition, you may also be given the data type of the target field. This is the standard type (e.g. string, int, boolean, dateTime, etc.) of the lowest level of nesting for the field. This is also an important consideration for the mapping: it will not make sense for you to give a high mapping score for a target field that has a datatype that is unrelated or unparsable to the data type of the source field. Some difference is acceptable but not for completely different types, for example boolean can't map to a date.
# In addition, there may also be a description of the target field. This is not present in all cases, but if it is present then please use this to help you better understand what this target field is referring to.
# You may also get additional information such as the possible accepted values for this target field, any validation logic for this field, or other information. Please use this information when making your mapping decision. 

# Here is some information about the source fields:
# The fields from the source schema are also custom complex nested objects. They will have two levels of nesting, for example: Contact.Preference.Method
# Similar to the target field, each layer of nesting of the source fields is an important consideration for whether these source fields will map well to the target field.
# Similar to the target field, you may also be given the data types of the source fields. These are the standard types (e.g. string, int, boolean, dateTime, etc.) of the lowest level of nesting for each source field. These are also an important consideration for the mapping: it will not make sense for you to give a high mapping score for a source field that has a datatype that is completely unrelated or unparsable to the data type of the target field. Some difference is acceptable but not for completely different types, for example boolean can't map to a date.



# The target field for this mapping job is:
# {target_string_row}



# And the source fields for this mapping job are:
# {unmapped_source_string_group}


# Based on your knowledge of the insurance industry, home insurance, motor insurance, pets, pet insurance, and other related insurance industry concepts and data structures, you will provide a mapping confidence level for each of the source fields that describes how well you think that source field would map to the target field.
# You must think very carefully about the mapping confidence level you apply for each source field, as it will be used in later process steps to implement the automated data migration pipelines, so any inaccuracies lead to very costly errors.

# Therefor you must also give a detailed reason for why you decided on that mapping confidence level

# The mapping confidence level you will apply must be a number between 1 and 5 where:
# 1 means there is a no chance that the source field matches the target field
# 2 means there is a small chance the source field matches the target field
# 3 means there is a good chance the source field matches the target field
# 4 means there is a very good chance the source field matches the target field
# 5 means there is a very very good chance the source field matches the target field

# You should decide on a mapping confidence level for each of the source fields, then set the mapping confidence level for each field using and use the value for source_field_unique_ref for each source field to reference it with its corresponding mapping confidence level as well as the reason for why you gave that confidence level.
# Then YOU MUST USE the available function set_source_field_mapping_confidence_levels in the set_source_field_mapping_confidence_levels_tool to set your mappings confidence level for each of the source fields.
# YOU MUST USE THIS FUNCTION."""

#     set_source_field_mapping_confidence_levels = generative_models.FunctionDeclaration(
#     name="set_source_field_mapping_confidence_levels",
#     description="""Sets the mapping confidence values for each source field for a given target field.

# Here is a general example to help you understand how to use the set_source_field_mapping_confidences_tool correctly. This is only an example to show the source and target field structures.:

# Assuming you had previously decided on the following mapping confidence levels (but it is important that you come up with your own values for mapping condifence level rather than specifically using these values):
# a mapping confidence level of 2 for the field with source_field_unique_ref=158
# a mapping confidence level of 1 for the field with source_field_unique_ref=159
# a mapping confidence level of 1 for the field with source_field_unique_ref=1290
# a mapping confidence level of 1 for the field with source_field_unique_ref=579
# a mapping confidence level of 1 for the field with source_field_unique_ref=638
# a mapping confidence level of 1 for the field with source_field_unique_ref=970
# a mapping confidence level of 1 for the field with source_field_unique_ref=3317
# a mapping confidence level of 3 for the field with source_field_unique_ref=160
# a mapping confidence level of 1 for the field with source_field_unique_ref=1910
# a mapping confidence level of 5 for the field with source_field_unique_ref=2280

# Then this function would be used to set the mapping confidence levels for each of the source fields, where your input parameter source_field_mapping_confidences would be:
# source_field_mapping_confidences = [
#     {'source_field_unique_ref':158,'mapping_confidence_level':'2'},
#     {'source_field_unique_ref':159,'mapping_confidence_level':'2'},
#     {'source_field_unique_ref':1290,'mapping_confidence_level':'1'},
#     {'source_field_unique_ref':579,'mapping_confidence_level':'1'},
#     {'source_field_unique_ref':638,'mapping_confidence_level':'1'},
#     {'source_field_unique_ref':970,'mapping_confidence_level':'1'},
#     {'source_field_unique_ref':3317,'mapping_confidence_level':'1'},
#     {'source_field_unique_ref':160,'mapping_confidence_level':'3'},
#     {'source_field_unique_ref':1910,'mapping_confidence_level':'1'},
#     {'source_field_unique_ref':2280,'mapping_confidence_level':'5'}
# ]""",

#     parameters={
#         "type": "object",
#         "properties": {
#             "source_field_mapping_confidences": {
#                 "type": "array",
#                 "description": "A List of objects where each object in the list contains the source field's source_field_unique_ref, the mapping_confidence_level for that source field and the reason for applying that mapping_confidence_level.",
#                 "items": {
#                     "type": "object",
#                     "properties": {
#                         "source_field_unique_ref": {
#                             "type": "integer",
#                             "description": "The reference ID for the source field."
#                         },
#                         "mapping_confidence_level": {
#                             "type": "string",
#                             "enum": ["1", "2", "3", "4", "5"],
#                             "description": "The confidence level for the mapping (an integer between 1 and 5)."
#                         },
#                         "mapping_confidence_level_reason": {
#                             "type": "string",
#                             "description": "The reason why the source field should have this mapping confidence level value"
#                         }
#                     },
#                     "required": ["source_field_unique_ref", "mapping_confidence_level", "mapping_confidence_level_reason"]
#                 }
#             },
#         },
#         "required": ["source_field_mapping_confidences"],
#     },
# )

######################
# BELOW IS FOR RUN 6 #
######################

#         prompt = f"""You are Data Engineer working for an insurance company. As part of a data migration project you need to assist with mapping fields in a source data schema fields in a target data schema. Your job is to provide a mapping confidence level for how well you think each of the fields for the source schemas you see will map to the field for the target schema.
# This will be used as part of an automated data migration process so your mapping confidence level describes how confident you are that the data in the source field could be directly loaded into this target field without modification and it would make logical sense and contextual sense for the data to be put into that target field.

# Here is some information about the source fields:
# The fields from the source schema are also custom complex nested objects. They will have two levels of nesting, for example: Contact.Preference.Method
# Similar to the target field, each layer of nesting of the source fields is an important consideration for whether these source fields will map well to the target field.
# Similar to the target field, you may also be given the data types of the source fields. These are the standard types (e.g. string, int, boolean, dateTime, etc.) of the lowest level of nesting for each source field. These are also an important consideration for the mapping.

# Here is some information about the target field:
# The field from the target schema is a custom complex nested object. It will be at a minimum one level of nesting, for example {target_df_row['Target_Level_1'].iloc[0]}.id, and at a maximum 4 layers of nesting, for example {target_df_row['Target_Level_1'].iloc[0]}.namedPerson.namedDriver.email.emailAddress.
# Each layer of nesting is a vary important consideration for whether the source fields will map well to this target field, for example, consider the target fields Client.person.dateOfBirth and Policy.namedPerson.namedPerson (Motor).dateOfBirth. Although these have the same value for their lowest level of nesting in the field type (dateOfBirth), as first is referencing the date of birth of the client of the policy because its top level object is Client, and the second is referring to a named driver thats been added to a motor policy (which is not necessarily the same person), because its top level object is Policy. This example is to show you that its VERY important that you consider the ENTIRE nested structure of the target field to decide on the mapping confidence level.
# In addition, you may also be given the data type of the target field. This is the standard type (e.g. string, int, boolean, dateTime, etc.) of the lowest level of nesting for the field. This is also an important consideration for the mapping.
# In addition, there may also be a description of the target field. This is not present in all cases, but if it is present then please use this to help you better understand what this target field is referring to.
# You may also get additional information such as the possible accepted values for this target field, any validation logic for this field, or other information. Please use this information when making your mapping decision. 

# You are being shown shown multiple fields in the source schema which are here:
# {unmapped_source_string_group}

# And one field from the target schema which is here:
# {target_string_row}

# Here is some information about how you should go about this job:
# Based on your knowledge of the insurance industry, home insurance, motor insurance, pets, pet insurance, and other related insurance industry concepts and data structures, you will provide a mapping confidence level for each of the source fields that describes how well you think that source field would map to the target field.
# You must think very carefully about the mapping confidence level you apply for each source field, as it will be used in later process steps to implement the automated data migration pipelines, so any inaccuracies lead to very costly errors.
# Remember that you need to consider EVERY NESTED LAYER of both the target field and the source fields to comprehend what kind of information they each represent, and therefore whether they are a good or bad mapping.
# As the value of the top level of the nested object of the target field is {target_df_row['Target_Level_1'].iloc[0]}, this means that the target field is only relevant to 
# {"the client that has taken out a policy." if target_df_row['Target_Level_1'].iloc[0] == 'Client' else ""}{"a household insurance or home insurance policy." if target_df_row['Target_Level_1'].iloc[0] == 'Household Policy' else ""}{"a motor insurance policy, or Motorcar policy data or car insurance data." if target_df_row['Target_Level_1'].iloc[0] == 'Motor Policy' else ""}{"a pet insurance policy, or the pet that is being insured against in the pet insurance policy." if target_df_row['Target_Level_1'].iloc[0] == 'Pet' else ""}{"a Policy that has been created or is being created by the client." if target_df_row['Target_Level_1'].iloc[0] == 'Policy' else ""}
# So you should only give high confidence mapping levels to source fields that also refer to {target_df_row['Target_Level_1'].iloc[0]} data. If you think the source field is not referring specifically to {target_df_row['Target_Level_1'].iloc[0]} data, you should not give a high mapping confidence level.
# You must also give a detailed reason for why you decided on that mapping confidence level.

# The mapping confidence level you will apply must be a number between 1 and 5 where:
# 1 means there is a no chance that the source field matches the target field
# 2 means there is a small chance the source field matches the target field
# 3 means there is a good chance the source field matches the target field
# 4 means there is a very good chance the source field matches the target field
# 5 means there is a very very good chance the source field matches the target field

# You should decide on a mapping confidence level for each of the source fields, then set the mapping confidence level for each field using and use the value for source_field_unique_ref for each source field to reference it with its corresponding mapping confidence level as well as the reason for why you gave that confidence level.
# Then YOU MUST USE the available function set_source_field_mapping_confidence_levels in the set_source_field_mapping_confidence_levels_tool to set your mappings confidence level for each of the source fields.
# YOU MUST USE THIS FUNCTION."""

#     set_source_field_mapping_confidence_levels = generative_models.FunctionDeclaration(
#         name="set_source_field_mapping_confidence_levels",
#         description="""Sets the mapping confidence values for each source field for a given target field.

# Here is a general example to help you understand how to use the set_source_field_mapping_confidences_tool correctly. This is only an example to show the source and target field structures.:

# Assuming you had previously decided on the following mapping confidence levels (but it is important that you come up with your own values for mapping condifence level rather than specifically using these values):
# a mapping confidence level of 2 for the field with source_field_unique_ref=158
# a mapping confidence level of 1 for the field with source_field_unique_ref=159
# a mapping confidence level of 1 for the field with source_field_unique_ref=1290
# a mapping confidence level of 1 for the field with source_field_unique_ref=579
# a mapping confidence level of 1 for the field with source_field_unique_ref=638
# a mapping confidence level of 1 for the field with source_field_unique_ref=970
# a mapping confidence level of 1 for the field with source_field_unique_ref=3317
# a mapping confidence level of 3 for the field with source_field_unique_ref=160
# a mapping confidence level of 1 for the field with source_field_unique_ref=1910
# a mapping confidence level of 5 for the field with source_field_unique_ref=2280

# Then this function would be used to set the mapping confidence levels for each of the source fields, where your input parameter source_field_mapping_confidences would be:
# source_field_mapping_confidences = [
#     {'source_field_unique_ref':158,'mapping_confidence_level':'2'},
#     {'source_field_unique_ref':159,'mapping_confidence_level':'2'},
#     {'source_field_unique_ref':1290,'mapping_confidence_level':'1'},
#     {'source_field_unique_ref':579,'mapping_confidence_level':'1'},
#     {'source_field_unique_ref':638,'mapping_confidence_level':'1'},
#     {'source_field_unique_ref':970,'mapping_confidence_level':'1'},
#     {'source_field_unique_ref':3317,'mapping_confidence_level':'1'},
#     {'source_field_unique_ref':160,'mapping_confidence_level':'3'},
#     {'source_field_unique_ref':1910,'mapping_confidence_level':'1'},
#     {'source_field_unique_ref':2280,'mapping_confidence_level':'5'}
# ]""",

#         parameters={
#             "type": "object",
#             "properties": {
#                 "source_field_mapping_confidences": {
#                     "type": "array",
#                     "description": "A List of objects where each object in the list contains the source field's source_field_unique_ref, the mapping_confidence_level for that source field and the reason for applying that mapping_confidence_level.",
#                     "items": {
#                         "type": "object",
#                         "properties": {
#                             "source_field_unique_ref": {
#                                 "type": "integer",
#                                 "description": "The reference ID for the source field."
#                             },
#                             "mapping_confidence_level": {
#                                 "type": "string",
#                                 "enum": ["1", "2", "3", "4", "5"],
#                                 "description": "The confidence level for the mapping (an integer between 1 and 5)."
#                             },
#                             "mapping_confidence_level_reason": {
#                                 "type": "string",
#                                 "description": "The reason why the source field should have this mapping confidence level value"
#                             }
#                         },
#                         "required": ["source_field_unique_ref", "mapping_confidence_level", "mapping_confidence_level_reason"]
#                     }
#                 },
#             },
#             "required": ["source_field_mapping_confidences"],
#         },
#     )