

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
-- sonnet 4.5

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