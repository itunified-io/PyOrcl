
# OEMNotification Class

The `OEMNotification` class is designed to handle Oracle Enterprise Manager (OEM) event notifications by sending email alerts. It dynamically extracts event details from environment variables provided by OEM and uses an SMTP server to send emails with configurable priorities and settings. The class supports both `.yaml` and `.ini` configuration formats, making it versatile for environments with or without the `pyyaml` module.

---

## Table of Contents
1. [Features](#features)
2. [Installation](#installation)
3. [Usage](#usage)
   - [Class Initialization](#class-initialization)
   - [Methods](#methods)
4. [Configuration](#configuration)
   - [YAML Configuration](#yaml-configuration)
   - [INI Configuration](#ini-configuration)
5. [Example](#example)
6. [Logging and Debugging](#logging-and-debugging)
7. [Creating a Virtual Environment](#creating-a-virtual-environment)

---

## Features
- **Dynamic Event Handling**: Automatically extracts event details such as event name, severity, target, and message from OEM environment variables.
- **Flexible Configuration**: Supports configuration from both YAML (`oemnotification.yaml`) and INI (`oemnotification.ini`) formats.
- **Configurable Rule Matching**: Supports two evaluation modes for rules:
  - `first_match`: Stops at the first matching rule.
  - `all_matches`: Applies all matching rules and combines results.
- **Dynamic Email Priority**: Sets email priority to "High" when the event severity is `URGENT`, otherwise defaults to "Normal."
- **Fallback Mechanism**: Automatically switches to `ConfigParser` for `.ini` files if `pyyaml` is not available.
- **Logging**: Provides detailed logging for debugging and monitoring email sending processes.
- **Modular Design**: Can be reused in various projects as a Python class.

---

## Installation
1. Clone the repository or copy the script file containing the `OEMNotification` class.

2. If using YAML configuration, install `pyyaml`:
   ```bash
   pip install pyyaml
   ```
   If not using `pyyaml`, ensure the configuration is provided in an `.ini` file.

---

## Usage

### Class Initialization
To use the `OEMNotification` class, initialize it with the appropriate configuration file:

```python
from oem_notification import OEMNotification

# For YAML configuration
notification = OEMNotification(config_file="oemnotification.yaml")

# For INI configuration
notification = OEMNotification(config_file="oemnotification.ini")
```

### Methods
1. **`get_event_details()`**
   - Extracts event details (`EVENT_NAME`, `SEVERITY`, `TARGET_NAME`, `TARGET_TYPE`, `LIFECYCLE_STATUS`, and `MESSAGE`) from the environment variables provided by OEM.
   - Returns a tuple of event attributes.

2. **`apply_rules(target_name, target_type, lifecycle_status)`**
   - Matches rules based on `target_name`, `target_type`, and `lifecycle_status`.
   - Returns the final list of recipients and email priority.

3. **`send_notification()`**
   - Sends an email notification using the SMTP configuration and extracted event details.
   - Automatically applies rules to determine recipients and email priority.

---

## Configuration

### YAML Configuration
Create a `oemnotification.yaml` file in the same directory as the script with the following structure:

```yaml
smtp:
  server: "your.smtp.server"
  port: 25
  sender: "oem@yourdomain.com"
  recipient: "default@yourdomain.com"

debug:
  debug: true
  debug_level: DEBUG

rules_evaluation: "all_matches"  # Options: "first_match", "all_matches"

rules:
  - condition:
      target_name: "all"
      target_type: "all"
      lifecycle_status: "mission critical"
    action:
      recipients:
        - "critical_team@yourdomain.com"
        - "team_leads@yourdomain.com"
      priority: "1"

  - condition:
      target_name: "dbserver01"
    action:
      recipients:
        - "db_admins@yourdomain.com"
      priority: "2"
```

### INI Configuration
Alternatively, create a `oemnotification.ini` file with the following structure:

```ini
[SMTP]
server = your.smtp.server
port = 25
sender = oem@yourdomain.com
recipient = default@yourdomain.com

[DEBUG]
debug = true
debug_level = DEBUG

[RULES]
evaluation_mode = all_matches

rule1.condition.target_name = all
rule1.condition.target_type = all
rule1.condition.lifecycle_status = mission critical
rule1.action.recipients = critical_team@yourdomain.com;team_leads@yourdomain.com
rule1.action.priority = 1

rule2.condition.target_name = dbserver01
rule2.action.recipients = db_admins@yourdomain.com
rule2.action.priority = 2
```

---

## Example
An example script to send a notification:

```python
from oem_notification import OEMNotification

# Create an instance of OEMNotification with YAML configuration
notification = OEMNotification(config_file="oemnotification.yaml")

# Send the notification
notification.send_notification()
```

---

## Logging and Debugging
The `OEMNotification` class uses Python's built-in `logging` module for debugging and error handling.

- If `debug` is set to `true` in the configuration file, the logger will output detailed debug information to a log file or the console.
- Errors and exceptions are logged with detailed stack traces for easier troubleshooting.

---

## Creating a Virtual Environment

It is recommended to run the `OEMNotification` script within a Python virtual environment to avoid conflicts with system-wide dependencies.

### Steps to Create and Activate a Virtual Environment:

1. **Create a Virtual Environment**:
   Run the following command in your project directory:
   ```bash
   python3 -m venv venv
   ```

2. **Activate the Virtual Environment**:
   - On Linux/macOS:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     .env\Scriptsctivate
     ```

3. **Install Dependencies**:
   Once the virtual environment is activated, install the required dependencies:
   ```bash
   pip install pyyaml
   ```

4. **Deactivate the Virtual Environment**:
   When you're done, deactivate the virtual environment by running:
   ```bash
   deactivate
   ```

Using a virtual environment ensures that the dependencies for this project are isolated from your system-wide Python installation.
