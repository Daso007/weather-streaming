Here's a summary of the real-time streaming data engineering project:
Project Objective:
To build an end-to-end real-time weather reporting system.
The system provides continuously updated weather information (temperature, conditions, air quality) for a chosen location.
It includes a crucial feature for sending real-time email alerts in case of extreme weather conditions.
Core Architecture & Components:
Data Source:
Uses the WeatherAPI.com free tier, which offers 1 million API calls per month.
Data Ingestion (Comparative Approach, settling on Azure Functions):
Initially explored both Azure Databricks and Azure Functions to ingest data from the Weather API and send it to Azure Event Hub.
An architectural decision was made to use Azure Functions for this project due to significant cost savings and sufficient performance for the given use case (simple API calls and data forwarding). The Azure Function App runs on a timer trigger (e.g., every 30 seconds) to fetch and send data.
Data Streaming:
Azure Event Hub is used as the central data streaming service to handle incoming real-time weather events from Azure Functions.
Real-time Data Processing & Loading (Microsoft Fabric):
Weather data is streamed from Event Hub into Microsoft Fabric.
Eventstream (in Fabric): An Eventstream pipeline is created to:
Connect to Azure Event Hub as an external source.
Continuously pull streaming weather data.
Load the data into a KQL Database (Kusto).
Eventhouse & KQL Database (in Fabric): An Eventhouse is created, which automatically provisions a KQL Database. This database is used to store the streaming time-series weather data. A table (e.g., "weather-table") is defined to hold the ingested records.
Data Reporting & Visualization:
Power BI is used to create interactive, real-time dashboards.
Reports are built on top of the data in the KQL Database.
Demonstrated creating reports both directly in the Power BI service (Fabric online) using Direct Query for real-time page refreshes, and using Power BI Desktop with Import Mode for more data transformation flexibility (requiring scheduled or manual refreshes).
KQL Query Sets (in Fabric): Used to query data from the KQL Database, acting like views, and form the basis for Power BI reports. A trick was shown to convert SQL queries to KQL using the explain feature in Fabric.
Real-time Alerting:
Data Activator (in Fabric): This component is configured to:
Monitor the KQL Database for specific alert conditions (e.g., non-empty 'alerts' field in the weather data received within the last minute).
Run KQL queries periodically (e.g., every 1 minute) to check for these conditions.
Trigger real-time email notifications when alerts are detected.
Security:
Azure Key Vault is used to securely store and manage sensitive information like API keys and connection strings.
Azure services (Databricks, Functions) are configured to retrieve these secrets securely from Key Vault, often using Managed Identities for Azure Functions.
Cost Management:
A key theme was cost optimization, notably in the decision to use Azure Functions over Azure Databricks for the ingestion part of this specific project.
The Azure Pricing Calculator was referenced to estimate resource costs.
Project Implementation Journey (Key Milestones):
Environment Setup:
Configuring the WeatherAPI.com data source and obtaining an API key.
Creating all necessary Azure resources within a dedicated Resource Group (e.g., Azure Function App, Event Hub, Key Vault, Microsoft Fabric capacity/trial).
Data Ingestion Development:
Detailed step-by-step implementation of data ingestion scripts in Python, first within Azure Databricks and then adapted for Azure Functions. This included API interaction, data parsing, and sending events to Event Hub.
Configuring authentication and authorization for services to interact (e.g., Function App access to Event Hub and Key Vault via Managed Identity).
Microsoft Fabric Integration:
Setting up the Eventhouse and KQL Database.
Building the Eventstream pipeline to connect Event Hub to the KQL Database.
Reporting & Analytics:
Writing KQL queries using Query Sets.
Developing Power BI reports for real-time data visualization.
Alerting Setup:
Creating KQL queries to identify alert conditions.
Configuring Data Activator to monitor these conditions and send email alerts.
End-to-End Testing:
Verifying the entire pipeline, ensuring data flows from the Weather API through Azure Functions, Event Hub, Fabric Eventstream, KQL Database, and finally to Power BI reports and Data Activator alerts.
