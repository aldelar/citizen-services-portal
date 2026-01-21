-- sonnet 4.5 unless noted

===== USE CASE ANALYSIS / REFININEMENT Assistance =====
-- Grok / Expert --

I'm trying to find an overarching scenario which would let us experience the value of connected services for things which are inherently disconnected today.
 
Thinking of the following:

- building permits and renovations
- Waste & Recycling Services
- Code Violation Reporting
- Utility Connection & Disconnection

I'm thinking a story/journey of someone trying to remodel a place.

Here's the project:
- upgrading power service from 200 amps to 400 amps
- redoing electrical wiring for the entire house
- switching gas furnace/AC to heatpump ductless throughout the house
- adding batteries and solar
- rebuilding roof (full metal roof)

This person would have to have a lot of government interactions to get this project going. Let's dig into the full process as it is stoday to document all the steps, and timeline, costs, etc. consider that some old appliances would have to be disposed, as well as materials (like old concrete roof tiles, furnace, electric cables, etc.).

Also consider a neighbor reporting an apparent code violation, and the process and time it would take for that violation to be known from the person remodeling, his ability to act on it and provide evidence of permits, etc. 

Let's say the neighbor reports a violation saying that the heat pump outdoor unit is to close to his property and too noisy (when they are not). What would happen during reporting, and so so...

The full story would show that such report is invalid.

Let's focus first on the full story, from project inception, to phasing all the steps, what docuemnts need to be filed, etc. and go thru the journey to completion and make sure we capture all the interaction points with the government entities.

After that, we will model how this could be re-engineered to be super efficient, but not yet. Let's focus on the present with a very documented process and steps.


======= ARCHITECTURE Assistance =======

(((1)))

We're going to start working on an overall architecture to support the synopsis.md project, and we'll be focusing on supporting what's described in the story-line as far as use cases to showcase the power of an AI powered governement platform at the service of citizens.

The architecture would need to be all hosted in Azure.
Here are some key services to use:
- Microsoft Fabric OneLake to store docs supporting governement services
- Microsoft Foundry as an AI platform, we'll use models deployed there, as well as leverage evaluations and tracing/monitoring once we have agents built. The agents will be built as Hosted Agents, on the Microsoft Agent Framework.
- Azure API Management in front of all models deployed so we have central policies for auth, governance and scalability of the services on top of multiple endpoints.
- Azure CosmosDB for the memory component of the agents
- Azure Container Apps for the application services (note that agents will be deployed as hosted agents in Foundry to benefit from agent specific services)
- Web front end built using React or any UI framework we might find more appropriate (availability of agent/chat specific components and simplicity of UI code will be a key decision factor)

Let's start by writing an overall summary of all this in the architecture.md document. Once reviewed, we'll work on detailing the components, services, and will generate some diagrams.

(((2)))

update the architecture to consider adding MCP servers. we will need to wrap the existing processes/websites/forms or mail-in processes and expose them via MCP servers to agents. we will also deploy the MCP servers in ACA (Azure Container Apps) and have them served behind APIM.

We should consider an MCP server registry (functionality available in APIM) to enable the entry agent to select the tools it needs to perform a specific job.

We want this system to be able to perform a lot of use cases supported by the agencies it has MCP tools for.

So the overall architecture should be tailored toward:
- exposing key service functinality from existing agencies / exposed as MCP tools / implementation will either use direct APIs where they exist, or trigger processes that will use email or request a human to mail in a form when needed
- build-up a plan of action when a citizen requests something, by leveraging all the knowledge it can gather from the official documentation, but also query the web to get insights from other citizens (like on reddit, etc.) if needed
- keep track of the plan of action, as citizen is expected to come back over the course of their project to complete steps, add more context, questions, etc.
- keep track of steps etc. for the purpose of deriving reports around types of asks from citizens, processes involved, time to proceed, etc.

Revise the overall plan.

Also, use mermaid when you diagram architecture or systems.



==== INFRASTRUCTURE DESIGN Assistance =====

Let's work on defining the Azure infrastrucure required for this project.

Let's write up the foundation services required for it. I'll provide a short list, and then please suggest a structure to build up an 'infra' folder that will contain all the biceps templates.

The goal is to be able to build and update the environment using 'azd'.

Here are the key services to define:
- resource group 'aldelar-ama'
- Foundry Service and one Foundry Resource to host the project - we will integrate API Management as the 'AI Gateway' to access models via the Gateway when we build agents
- AI Search service
- API Management (will be used for model endpoints to enforce governance, capacity and enable scale out accross regions of models)
- Azure Container Apps (So we can host mcp servers and the web apps)
- Azure Content Safety
- Azure Cosmos DB as our memory store for agents + overall citizen operational data store

Let's start here. Draft a landing zone document in 'infrastructure.md', make some assumptions based on best practices, but be brief, and let's discuss the open questions to refine this.

Propose how to lay out the biceps files. Don't write any bicept file yet, we will do that once we agree on scope of services required and requirements.

===== MCP servers / LADBS DEPLOYMENT Assistance =====

I've added under src/mcp-servers/ladbs a first skeleton of an MCP server for the LADBS functionality for this project.

Can you review what's in there, and suggest ways to organize this. If we are to need more services for this server, how would we go about organizing the bicepts for it. Do we need an 'mcp' folder under infra?

What would you have within the src/mcp-servers/ladbs folder to help dev/test? Should we have a mini README.md there and some instructions to test?

I want to use uv for python env management to speed up dev/test.


===== FOUNDRY/APIM/AGENT SETUP

great. now, let's work on the foundry setup.

Please suggest an approach to get the following done:

we need the 2 gpt models deployed, on top of that, update the readme and indicate we'll need an embedding model as well, and for that we'll use 'text-embedding-3-small' from openai. so define how to package these models into the infra deployment
we also want to have APIM setup to have one endpoint defined for each of these models, as we're going to want to access them via APIM. setup will some basic defaults, we will tune that later
we also want APIM to define an endpoint for the LADBS MCP server, and apply basic defaults to that
we will want to define a Foundry Project called 'citizens-services-portal'
in foundry, we will want to define an AI Gateway that will connect to our APIM instance
in that project, we will want to setup a Tool that will connect to our deployed MCP server (accessed via APIM), that tool will be called 'mcp-ladbs'
then, we'll want to define a Foundry Declarative Agent (Using the Agent Service in Foundry), which will be setup with the mcp-ladbs tool, and use the gpt-5.2 model served by its APIM endpoint (this will need to use the Gateway setup above)
Please let me know how you would approach all this, all this setup should use azd, and the agent code/artifacts required to define this should be stored in srv/agents/ladbs. I assumed we'll have a file for the system prompt so it's sourced controlled, some yaml definition of the agent to be deployed using azd or azure cli if azd doesn't support it, etc.

Propose the cleanests approaches to do all this so we can have our first agent up and running.


=======

How's the MCP_LADBS_URL retrieved from config?
We have to make sure it's done in a programmatic way, meaning if the ladbs agent were to require a tool named 'abc', we would know how to fetch the deployment configs using azd to retrieve the ACA deployed URL for that tool, assuming the tools are all deployed before we deploy the agents.

Can you double check all this, make sure the deploy order is correct, and that from the tool 'name' only, we can retrieve the URL via deployed items to make this all work at scale.