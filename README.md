🌦️ Real-Time Weather Reporting System (Streaming Data Engineering Project)
🚀 Project Objective
To build an end-to-end real-time weather reporting system that continuously updates weather metrics such as:

🌡️ Temperature

🌬️ Conditions

🧪 Air Quality

It also includes real-time email alerts for extreme weather conditions.

🧱 Core Architecture & Components
🔗 Data Source
API: WeatherAPI.com (Free tier – 1 million API calls/month)

⚙️ Data Ingestion (Comparative Approach)
Explored two ingestion options:

Azure Databricks

Azure Functions ✅ (Final choice)

Why Azure Functions?

Cost-effective

Timer-triggered every 30 seconds

Lightweight for simple API polling and forwarding

🔄 Data Streaming
Service Used: Azure Event Hub

Purpose: Receives real-time weather events from Azure Functions

🔥 Real-Time Processing in Microsoft Fabric
📡 Eventstream Pipeline
Connects Event Hub to Fabric

Continuously pulls weather data

Loads into a KQL Database

🏠 Eventhouse & KQL Database
Automatically provisioned with Eventstream

Stores time-series weather data

Table: weather_table (schema for ingested records)

📊 Data Reporting & Visualization
🔍 Power BI Integration
Real-time dashboards using:

Direct Query (Fabric online) for live updates

Import Mode (Power BI Desktop) for richer transformation

🔎 KQL Query Sets
Act like SQL Views

Support Power BI reporting

Can convert SQL to KQL using EXPLAIN in Fabric

🔔 Real-Time Alerting
📬 Data Activator (in Microsoft Fabric)
Monitors KQL Database for:

Non-empty alerts field

Records received within the last minute

Triggers real-time email alerts

Runs checks every 1 minute using KQL

🔐 Security Practices
🔑 Azure Key Vault stores:

API Keys

Connection Strings

🛡️ Secure access with Managed Identity for Azure Functions

💸 Cost Optimization
Azure Functions selected over Databricks for ingestion to reduce cost

Estimated using Azure Pricing Calculator

🛠️ Project Implementation Journey
🧰 Environment Setup
Registered at WeatherAPI.com and obtained API key

Created Azure Resources:

Azure Function App

Event Hub

Key Vault

Microsoft Fabric Trial/Capacity

🧪 Data Ingestion Development
Developed and tested ingestion code in:

Azure Databricks (initially)

Azure Functions (final version)

Features:

API call logic

JSON parsing

Event Hub message sending

Configured service access via Managed Identity

📈 Microsoft Fabric Integration
Setup Eventstream to move data from Event Hub to KQL Database

Created and configured Eventhouse

📉 Reporting & Analytics
Wrote KQL queries for metrics and alerts

Built dashboards in Power BI

📨 Alerting Mechanism
Wrote KQL queries to detect extreme weather

Configured Data Activator to send emails in real-time

✅ End-to-End Testing
Verified entire flow:
Weather API → Azure Functions → Event Hub → Microsoft Fabric (Eventstream & KQL DB) → Power BI → Data Activator (Email Alerts)

📁 Tech Stack
Layer	Tools/Services
Data Source	WeatherAPI.com
Ingestion	Azure Functions
Streaming	Azure Event Hub
Processing	Microsoft Fabric (Eventstream, KQL DB)
Visualization	Power BI
Alerting	Microsoft Fabric - Data Activator
Security	Azure Key Vault, Managed Identities

🙌 Acknowledgments
Microsoft Fabric team for public documentation and examples

WeatherAPI for offering a generous free tier

Azure Pricing Calculator for guiding cost decisions

📬 Contact
If you’d like to know more about this project or explore the code/configurations, feel free to reach out:

Dibyajyoti Datta
📧 dibyajyotidatta410@gmail.com
🌐 LinkedIn

