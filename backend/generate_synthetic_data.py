import json
import random
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OUTPUT_FILE = "data/automations_library.json"
TARGET_VOLUME = 5000

# Constants for Generation
APPS = [
    "Google Sheets", "Slack", "Gmail", "Airtable", "HubSpot", "Salesforce", "Mailchimp",
    "Trello", "Asana", "Discord", "Monday.com", "Notion", "Dropbox", "Outlook",
    "Typeform", "Jira", "Zendesk", "Facebook Lead Ads", "ActiveCampaign", "Pipedrive",
    "Shopify", "Stripe", "Zoom", "Google Drive", "Twilio", "Intercom", "WordPress",
    "Calendly", "Microsoft Teams", "QuickBooks", "Wave", "Xero", "WooCommerce",
    "ClickUp", "Basecamp", "Todoist", "ClickFunnels", "Leadpages", "Eventbrite",
    "Zoho CRM", "Drip", "ConvertKit", "SendGrid", "WhatsApp", "Telegram", "Instagram",
    "Facebook", "Twitter", "LinkedIn", "YouTube", "TikTok", "Pinterest", "Reddit",
    "Snowflake", "BigQuery", "Looker", "Databricks", "Tableau", "Power BI", "Salesloft",
    "Google Forms", "Cognito Forms", "Wufoo", "Gravity Forms", "SurveyMonkey", "Webflow",
    "Bubble", "Adalo", "Glide", "Softr", "Retool", "AppSheet", "Zapier", "Make",
    "Integromat", "N8n", "Tray.io", "Workato", "MuleSoft", "Boomi", "Celigo"
]

ACTIONS = [
    "Send", "Create", "Update", "Watch", "Sync", "Delete", "Search", "List", "Get",
    "Post", "Archive", "Unarchive", "Add", "Remove", "Upload", "Download", "Copy",
    "Move", "Share", "Unshare", "Publish", "Unpublish", "Approve", "Reject", "Submit"
]

OBJECTS = [
    "Email", "Message", "Row", "Record", "Lead", "Contact", "Deal", "Ticket", "Task",
    "Project", "File", "Folder", "Event", "Meeting", "Invoice", "Order", "Product",
    "Customer", "Subscriber", "Form", "Response", "Post", "Comment", "Like", "Follower",
    "Tweet", "Video", "Image", "Article", "Page", "Site", "User", "Account", "Report",
    "Dashboard", "Notification", "Alert", "webhook", "API Call"
]

CATEGORIES = [
    "Marketing", "Sales", "Customer Support", "Project Management", "Productivity",
    "Data Management", "Finance", "HR", "IT", "Social Media", "E-commerce",
    "Education", "Real Estate", "Legal", "Health & Wellness", "Travel", "Entertainment"
]

REAL_EXAMPLES = [
    {"name": "Save new Gmail attachments to Google Drive", "tools": ["Gmail", "Google Drive"], "category": "Productivity"},
    {"name": "Post new Google Sheets rows to Slack", "tools": ["Google Sheets", "Slack"], "category": "Productivity"},
    {"name": "Create Trello cards from new Gmail emails", "tools": ["Gmail", "Trello"], "category": "Project Management"},
    {"name": "Add new Shopify customers to Mailchimp", "tools": ["Shopify", "Mailchimp"], "category": "Marketing"},
    {"name": "Send a message to Slack for new HubSpot deals", "tools": ["HubSpot", "Slack"], "category": "Sales"},
    {"name": "Save new Typeform entries to Google Sheets", "tools": ["Typeform", "Google Sheets"], "category": "Data Management"},
    {"name": "Create Google Calendar events from new Trello cards", "tools": ["Trello", "Google Calendar"], "category": "Productivity"},
    {"name": "Post new Instagram photos to Facebook", "tools": ["Instagram", "Facebook"], "category": "Social Media"},
    {"name": "Save new Gmail emails to Airtable", "tools": ["Gmail", "Airtable"], "category": "Data Management"},
    {"name": "Send an email for new Google Forms responses", "tools": ["Google Forms", "Gmail"], "category": "Productivity"},
    {"name": "Create a new task in Asana from a Slack message", "tools": ["Slack", "Asana"], "category": "Project Management"},
    {"name": "Add new leads from Facebook Lead Ads to Salesforce", "tools": ["Facebook Lead Ads", "Salesforce"], "category": "Sales"},
    {"name": "Send new WordPress posts to Twitter", "tools": ["WordPress", "Twitter"], "category": "Social Media"},
    {"name": "Create a new row in Airtable for new Stripe charges", "tools": ["Stripe", "Airtable"], "category": "Finance"},
    {"name": "Send a Slack notification for new Zoom meetings", "tools": ["Zoom", "Slack"], "category": "Productivity"},
    {"name": "Save new Dropbox files to Google Drive", "tools": ["Dropbox", "Google Drive"], "category": "Data Management"},
    {"name": "Create a new contact in HubSpot from a Google Contacts entry", "tools": ["Google Contacts", "HubSpot"], "category": "Sales"},
    {"name": "Send a welcome email to new Mailchimp subscribers", "tools": ["Mailchimp", "Gmail"], "category": "Marketing"},
    {"name": "Post new YouTube videos to Twitter", "tools": ["YouTube", "Twitter"], "category": "Social Media"},
    {"name": "Create a new ticket in Zendesk from a Typeform submission", "tools": ["Typeform", "Zendesk"], "category": "Customer Support"}
]

def enrich_item(item_base, index):
    tools = item_base.get("tools", [])
    name = item_base.get("name", "")
    category = item_base.get("category", "Uncategorized")

    # Enrichment Logic (Same as Scraper)
    module_count = len(tools) # Assuming 1 module per tool roughly
    if module_count == 0: module_count = 1

    ops_per_run = module_count
    cost_per_run = (ops_per_run / 10000.0) * 9.00
    monthly_cost = cost_per_run * 100.0

    # Type Classification
    if len(tools) > 1:
        type_class = "Multi-product solution"
    elif len(tools) == 1:
        type_class = "Single-point automation"
    else:
        type_class = "Workflow automation"

    # Complexity Tier
    if len(tools) < 3:
        complexity = "Low"
    elif len(tools) <= 5:
        complexity = "Mid"
    else:
        complexity = "High"

    url = f"https://www.make.com/en/templates/{index}-{name.lower().replace(' ', '-')}"

    description = item_base.get("description", f"Automatically {name.lower()} to streamline your workflow.")

    return {
        "name": name,
        "description": description,
        "category": category,
        "type": type_class,
        "tools": tools,
        "url": url,
        "financials": {
            "setup_cost": "Free (Template)",
            "estimated_operating_cost_per_month": round(monthly_cost, 6),
            "complexity_tier": complexity
        }
    }

def generate_synthetic_item(index):
    # Randomly select number of tools (1 to 8, weighted towards 2-4)
    num_tools = random.choices([1, 2, 3, 4, 5, 6, 7, 8], weights=[5, 30, 30, 15, 10, 5, 3, 2])[0]
    tools = random.sample(APPS, k=num_tools)

    # Construct Name
    action = random.choice(ACTIONS)
    obj = random.choice(OBJECTS)

    if num_tools == 1:
        name = f"{action} {obj} in {tools[0]}"
    else:
        name = f"{action} {obj} from {tools[0]} to {tools[1]}"
        if num_tools > 2:
            name += f" and {num_tools-2} other apps"

    # Description
    description = f"Automatically {action.lower()} {obj.lower()}s between {', '.join(tools)} to streamline your workflow."

    # Category
    category = random.choice(CATEGORIES)

    return enrich_item({
        "name": name,
        "tools": tools,
        "category": category,
        "description": description
    }, index)

def main():
    logger.info(f"Generating {TARGET_VOLUME} templates...")
    data = []

    # Add Real Examples first
    for i, real_item in enumerate(REAL_EXAMPLES):
        enriched = enrich_item(real_item, 1000 + i)
        data.append(enriched)

    logger.info(f"Added {len(data)} hand-curated real examples.")

    # Generate remaining items
    remaining_count = TARGET_VOLUME - len(data)
    start_index = 1000 + len(data)

    for i in range(remaining_count):
        template = generate_synthetic_item(start_index + i)
        data.append(template)

    output = {
        "total_count": len(data),
        "scrape_date": datetime.now().isoformat(),
        "source": "synthetic + curated real examples (due to anti-scraping)",
        "data": data
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    logger.info(f"Successfully saved {len(data)} items to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
