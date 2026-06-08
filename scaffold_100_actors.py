import os
import textwrap

PLATFORMS = [
    # ERP/CRM
    "sap", "oracle", "workday", "servicenow", "hubspot",
    "dynamics365", "netsuite", "zendesk", "zoho", "pipedrive",
    # Office/Productivity
    "m365", "google-workspace", "slack", "notion", "asana",
    "monday", "trello", "atlassian", "box", "dropbox",
    # Design/CAD
    "adobe", "figma", "autodesk", "canva", "sketch",
    "invision", "miro", "blender", "rhino", "solidworks",
    # Cloud/Infra
    "aws", "azure", "gcp", "cloudflare", "digitalocean",
    "heroku", "vercel", "netlify", "linode", "ovh",
    # Data/BI
    "snowflake", "databricks", "tableau", "powerbi", "looker",
    "splunk", "elastic", "mongodb", "redis", "kafka",
    # Fintech
    "stripe", "square", "paypal", "plaid", "adyen",
    "coinbase", "brex", "ramp", "billcom", "xero",
    # Healthcare
    "epic-systems", "cerner", "athenahealth", "eclinicalworks", "allscripts",
    "meditech", "nextgen", "drchrono", "curemd", "greenway",
    # Retail/E-commerce
    "shopify", "magento", "bigcommerce", "woocommerce", "sf-commerce",
    "square-retail", "lightspeed", "wix-stores", "ecwid", "vtex",
    # DevTools
    "github", "gitlab", "bitbucket", "docker", "kubernetes",
    "terraform", "jenkins", "circleci", "postman", "datadog",
    # Niche
    "zoom", "twilio", "sendgrid", "mailchimp", "docusign",
    "intercom", "airtable", "typeform", "calendly"
]

ACTORS_DIR = "/Users/junkawasaki/github/etzhayyim-root/20-actors"

def scaffold():
    os.makedirs(ACTORS_DIR, exist_ok=True)

    for platform in PLATFORMS:
        actor_name = f"{platform}-compat"
        actor_dir = os.path.join(ACTORS_DIR, actor_name)
        src_dir = os.path.join(actor_dir, "src")
        schema_dir = os.path.join(actor_dir, "schema")

        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(schema_dir, exist_ok=True)

        # README.md
        readme_content = textwrap.dedent(f"""\
            # {platform.capitalize()} Clean Room Actor

            This actor provides a clean-room, API-compatible implementation of the {platform.capitalize()} platform.

            ## Architecture
            - **State:** Backed by Datomic for immutable, time-travel-capable record keeping.
            - **Schema:** Defined in `schema/{platform}.kotoba`.
            - **Execution:** Runs in `Py Kotodama WASM`, intercepting inbound REST requests.
        """)
        with open(os.path.join(actor_dir, "README.md"), "w") as f:
            f.write(readme_content)

        # deps.toml
        deps_content = textwrap.dedent(f"""\
            [project]
            name = "{actor_name}"
            version = "0.1.0"
            description = "Clean room {platform.capitalize()} compatible actor"

            [dependencies]
            kotoba = "workspace"
            kotodama-wasm = "workspace"
            datomic-client = "workspace"
        """)
        with open(os.path.join(actor_dir, "deps.toml"), "w") as f:
            f.write(deps_content)

        # schema/<name>.kotoba
        kotoba_content = textwrap.dedent(f"""\
            // {platform.capitalize()} Core Object Schema Mapping to Datomic

            namespace {platform} {{

                entity CoreObject {{
                    id: string @unique
                    name: string @index
                    createdAt: datetime
                    updatedAt: datetime
                }}
            }}
        """)
        with open(os.path.join(schema_dir, f"{platform}.kotoba"), "w") as f:
            f.write(kotoba_content)

        # src/main.py
        main_py_content = textwrap.dedent(f"""\
            \"\"\"
            Py Kotodama WASM entrypoint for {platform.capitalize()} Compat Actor.
            \"\"\"

            from kotodama import Runtime
            from kotoba import load_schema
            from datomic import DatomicClient

            # Initialize environment
            schema = load_schema("../schema/{platform}.kotoba")
            db = DatomicClient.connect()

            app = Runtime("{actor_name}")

            @app.route("/api/v1/query", methods=["GET"])
            def execute_query(request):
                \"\"\"
                Emulate the {platform.capitalize()} API endpoint.
                \"\"\"
                query = request.query_params.get("q")
                if not query:
                    return {{"error": "MALFORMED_QUERY", "message": "query parameter 'q' is required"}}, 400

                # Stub: Clean Room implementation
                return {{
                    "totalSize": 0,
                    "done": True,
                    "records": []
                }}

            if __name__ == "__main__":
                app.start()
        """)
        with open(os.path.join(src_dir, "main.py"), "w") as f:
            f.write(main_py_content)

if __name__ == "__main__":
    scaffold()
    print("Successfully generated 99 actors.")
