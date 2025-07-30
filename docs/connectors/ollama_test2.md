
# Configuring DemoCRM API Connector

This connector allows you to interact with the DemoCRM API, enabling integration with various applications. To make use of this connector, you'll need to have an API key from your DemoCRM account.

## Prerequisites
1. Create an API key in DemoCRM.
   2. Install the required libraries for the connector
   


## Connector Setup
Below table lists the fields shown in the connector configuration form.

| Field | Description |
|-------|-------------|
| **API Key** | Token for requests obtained from your DemoCRM account || **Base URL** | The base URL of the DemoCRM API (e.g., https://api.democrm.com) |


## Connector Parameters

### Authentication
| Technical Name | Type | Default | Example | Description |
|---------------|------|---------|---------|-------------|
| api_key | String |  | abc123 | Your DemoCRM API key || base_url | String |  | https://api.democrm.com | The base URL of your DemoCRM API |




## Extracted Data
### Tables
| Table | Column | Data Type |
|-------|--------|-----------|
| **customers** | - | - |
|  | id | String |
|  | email | String |


*Generated automatically — 2025-07-29T01:38:03.425715Z*