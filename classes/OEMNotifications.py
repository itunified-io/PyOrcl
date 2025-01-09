"""
Oracle Enterprise Manager Notification Script

This script is used to send email notifications for events triggered in Oracle Enterprise Manager (OEM).
It dynamically extracts event information from environment variables provided by OEM and configuration from a YAML or INI file.

Author: Benjamin Buechele
Company: ITUNIFIED
GitHub: https://github.com/itunified-io/PyOrcl
License: GPL v3 (see LICENSE file for details)

Description:
- Extracts event details from OEM environment variables.
- Sends email notifications using an SMTP server.
- Supports dynamic priority headers based on event severity.

Configuration:
- Ensure a configuration file is available:
  - `config/oemnotifications.yaml` for Python version >= 3.
  - `config/configurations.ini` for Python version <= 2.7.

License:
- This project is licensed under the GNU General Public License v3.0.
- See the LICENSE file in the repository for detailed terms and conditions.

Issues:
- To report issues or request features, visit the GitHub repository:
  https://github.com/itunified-io/PyOrcl/issues
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText

# Check Python version and select appropriate configuration handler
try:
    import yaml
    CONFIG_MODE = "yaml"
except ImportError:
    from ConfigParser import ConfigParser
    CONFIG_MODE = "ini"


class OEMNotification:
    """
    A class to handle Oracle Enterprise Manager (OEM) event notifications via email with custom rules.
    """

    def __init__(self, config_file=None):
        # Determine the config file path
        project_root = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(project_root, "config")
        default_config_file = "oemnotification.yaml" if CONFIG_MODE == "yaml" else "oemnotification.ini"
        config_file = config_file or os.path.join(config_dir, default_config_file)

        # Load configuration
        if CONFIG_MODE == "yaml":
            self.config = self.load_yaml_config(config_file)
        else:
            self.config = self.load_ini_config(config_file)

        # Extract SMTP configuration
        smtp_config = self.config.get("smtp", {})
        self.smtp_server = smtp_config.get("server")
        self.smtp_port = int(smtp_config.get("port", 25))
        self.smtp_sender = smtp_config.get("sender")
        self.smtp_recipient = smtp_config.get("recipient")

        # Debug configuration
        debug_config = self.config.get("debug", {})
        self.debug = debug_config.get("debug", False)
        self.debug_level = debug_config.get("debug_level", "INFO").upper()

        # Rule evaluation mode: "first_match" or "all_matches"
        self.rules_evaluation = self.config.get("rules_evaluation", "all_matches").lower()

        # Configure logging
        log_file = os.path.join(project_root, "oem_notification.log") if self.debug else None
        self.configure_logging(log_file, self.debug_level)

        self.logger.debug(f"Loaded configuration: {self.config}")

    @staticmethod
    def configure_logging(log_file=None, debug_level="INFO"):
        """
        Configures the logging system. Logs to file if `log_file` is provided, otherwise logs to console.
        """
        log_level = getattr(logging, debug_level, logging.INFO)
        handlers = [logging.FileHandler(log_file)] if log_file else [logging.StreamHandler()]

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=handlers,
        )

    def load_yaml_config(self, config_file):
        """
        Load configuration from a YAML file dynamically.
        """
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file '{config_file}' not found.")
        
        with open(config_file, "r") as file:
            config = yaml.safe_load(file)
        
        if not isinstance(config, dict):
            raise ValueError(f"Configuration file '{config_file}' is not in the expected YAML format.")
        
        return config

    def load_ini_config(self, config_file):
        """
        Load configuration from an INI file dynamically, including rules.
        """
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file '{config_file}' not found.")
        parser = ConfigParser()
        parser.read(config_file)

        config = {
            "smtp": {
                "server": parser.get("SMTP", "server"),
                "port": parser.get("SMTP", "port"),
                "sender": parser.get("SMTP", "sender"),
                "recipient": parser.get("SMTP", "recipient"),
            },
            "debug": {
                "debug": parser.getboolean("DEBUG", "debug", fallback=False),
                "debug_level": parser.get("DEBUG", "debug_level", fallback="INFO").upper(),
            },
            "rules_evaluation": parser.get("RULES", "evaluation_mode", fallback="all_matches").lower(),
            "rules": [],
        }

        # Parse rules dynamically
        for key in parser.options("RULES"):
            if key.startswith("rule"):
                rule_id, attr = key.split(".", 1)
                rule_index = int(rule_id.replace("rule", ""))
                while len(config["rules"]) < rule_index:
                    config["rules"].append({"condition": {}, "action": {}})
                
                if attr.startswith("condition."):
                    condition_key = attr.replace("condition.", "")
                    config["rules"][rule_index - 1]["condition"][condition_key] = parser.get("RULES", key)
                elif attr.startswith("action."):
                    action_key = attr.replace("action.", "")
                    value = parser.get("RULES", key)
                    if action_key == "recipients":
                        value = value.split(";")  # Split multiple recipients by `;`
                    config["rules"][rule_index - 1]["action"][action_key] = value

        return config

    def get_event_details(self):
        """
        Extract event details from environment variables.
        """
        event_details = {key: value for key, value in os.environ.items()}

        # Log all environment variables
        self.logger.debug("Extracted Environment Variables:")
        for key, value in event_details.items():
            self.logger.debug(f"  {key}: {value}")

        # Return specific event details (defaults if not present)
        return (
            event_details.get("EVENT_NAME", "Unknown Event"),
            event_details.get("SEVERITY", "Unknown Severity"),
            event_details.get("TARGET_NAME", "Unknown Target"),
            event_details.get("TARGET_TYPE", "Unknown Type"),
            event_details.get("LIFECYCLE_STATUS", "Unknown Status"),
            event_details.get("MESSAGE", "No details provided."),
        )

    def apply_rules(self, target_name, target_type, lifecycle_status):
        """
        Apply rules based on target_name, target_type, and lifecycle_status.
        The behavior depends on the rules_evaluation setting: "first_match" or "all_matches".
        """
        recipients = [self.smtp_recipient]
        priority = "3"  # Default priority (Normal)

        for rule in self.config.get("rules", []):
            condition = rule.get("condition", {})
            action = rule.get("action", {})

            # Check conditions
            match_target_name = condition.get("target_name", "").lower() in ["all", target_name.lower()]
            match_target_type = condition.get("target_type", "").lower() in ["all", target_type.lower()]
            match_lifecycle_status = condition.get("lifecycle_status", "").lower() in ["", lifecycle_status.lower()]

            if match_target_name and match_target_type and match_lifecycle_status:
                # Merge recipients
                new_recipients = action.get("recipients", [])
                recipients.extend(new_recipients)
                recipients = list(set(recipients))  # Ensure unique recipients

                # Set priority to the highest matching rule (lower number = higher priority)
                priority = min(priority, action.get("priority", priority), key=int)

                self.logger.debug(f"Rule applied: {rule}")

                # Stop if "first_match" mode is active
                if self.rules_evaluation == "first_match":
                    break

        return recipients, priority

    def send_notification(self):
        """
        Sends an email notification using the extracted event details.
        """
        # Get event details
        event_name, event_type, target_name, target_type, lifecycle_status, event_message = self.get_event_details()

        # Apply notification rules
        recipients, priority = self.apply_rules(target_name, target_type, lifecycle_status)

        # Prepare subject and body
        subject = f"OEM Alert: {event_name} - {event_type} on {target_name} ({lifecycle_status})"
        body = f"""
        Oracle Enterprise Manager Event Notification

        Event Name: {event_name}
        Event Type: {event_type}
        Target: {target_name}
        Target Type: {target_type}
        Lifecycle Status: {lifecycle_status}

        Details:
        {event_message}

        Please address this issue promptly.
        """

        # Create email message
        msg = MIMEText(body)
        msg["From"] = self.smtp_sender
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg["X-Priority"] = priority
        msg["Importance"] = "High" if priority == "1" else "Normal"
        msg["Priority"] = "urgent" if priority == "1" else "normal"

        # Send the email
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                self.logger.debug(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
                server.sendmail(self.smtp_sender, recipients, msg.as_string())
                self.logger.info(f"Email successfully sent to {recipients}.")
        except Exception as e:
            self.logger.error(f"Error sending email: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        # Create notification instance and send email
        notification = OEMNotification()
        notification.send_notification()
    except Exception as e:
        logging.error(f"Critical error: {e}", exc_info=True)
