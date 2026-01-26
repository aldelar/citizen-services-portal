## DO NOT USE THIS FOR THIS PROJECT / JUST TRACKING PURPOSES, PERSONAL NOTES

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




===== ARCHITECTURE REVIEW Assistance =====

Let's work on the architecture to support this project. Please look at 1-synopis.md, 2-use-cases.md for the long term goals.

We will focus on architecting to support 3-demo-story-line.md, which relies on 3 government agencies.

Look at the 4-architecture.md document. We want to review it for corecteness, suggest changes in the approach. The goal is to keep things simple yet powerful and extensible.

A few things I'm thinking about:
- MCP tools to support existing online services (online forms: we'll assume there is a backend API that supports them, and that we could submit such requests via an MCP tool)
- A need to deal with things which only currently have paper form (is there any in our story line?) or phone call? -> how do we want to deal with that?
- Do we assume that each government agency will deliver its own agent, should they be hosted as single agents
- How do we build a cross agency agent that enables to deliver the story line use case as one government interaction?

Each agency probably has its own definition of a user (no sharing). Do we deal with that, or do we suggest shared services to streamline all of it.

As part of the review, make sure we strip down the services offered by the MCP servers to the bare minimum to satisfy the story.

Do not implement anything, let's discuss. Create a 4-architecture-v2.md file to help collect thoughts and refine things as needed.

==

Good work, let's continue to try to simplify things:
- Let's drop the violation sub-plot to simplify the story and tools
- web research: let's drop it, but this assume we'll collect all necessary documents related to processes, etc from each agency to index them as vector dbs, please include that in the architecture
- agencies could eventually offer agents... let's not prototype this, but we will document how this architecture can be extended. agree that for now, agencies just need to offer MCP tools. should their MCP tools offer access to their processes documents? how do we solve for this? it seems like each agency would be responsible for offering all their docs/policies/etc as a knowledge source... how do we handle that in the architecture for scalability and to let agencies stay independent from each other
- the UI should be minimal, but the power comes from seeing the overall plan, and tracking progress? how can we build something that is able to track a (JSON) plam, dusplay it (and relate the current state/status of things). the plan should be able to adjust as new information comes in
- for anything for which there isn't an online form, we should go with the route of telling the use what to do, and assist with preparing the content of an email, etc and tell them what to do next... this step would then be assigned to the user, and the system would need to check once in a while with the user if things got done, and copy/paste of upload what they got back from that process
- do we have a requirement for each MCP tool to have specific tools like: operations_not_supported_online.... how do we figure out what is supported online vs requires user to take action. we can do the search now, and establish these tools, or do we define an MCP contract so to speak, which each agency will need to implement to list all services they can take care of but are not automated yet? thoughts?

Let's work on that first for a new pass. Suggest other simplifications.




======= BUILDING KNOWLEDGE BASES Assistance =====

(see Github Copilot Issue to see how knewledge bases were researched)

I want you to process the /assets/agency-knowledge-base-document-inventory.md file, and download all documents listed there (PDFs, and for HTML, download them as well) and place them into the appropriate respective folders (/assets/ladbs, etc.)




====== UI framework Assistance ======

Create an Issue in the repo to do some research about best UI framework to select to implement this solution. We'd be looking for something that provides a lot of good widgets/patterns for our requirements (chat application, with some rich visuals, as well as composed views with right panel for project diagram overview, mid panel for chat, left panel likely to select projects (collapsible bar)).

I am a python developer, so python friendly preferred.

This framework doesn't have to be something we'd use for production, the goal is speed and simplicity to demonstrate the concepts of the underlying implementation and project.

Can you do a research around what's used for most project, analyze their strengths against our requirements here and propose a selection or a few choices? Ask questions in your final report if options are open and depend on priorities not clearly defined yet.

Create the issue, and create a system prompt assist for the agent I'm going to delegate it to (github agent) to make sure the task stays on track and deliver maximum value so we quickly select the right framework.




== UI wireframes Creation Assistance =====

See GitHub




==== UI WIREFRAMES REfinement Assistance =====

We've selected NiceGUI as the UI framework for this project, do some research around the functionality of this framework, and review all the wireframes under /docs/ui-wireframes.

I'd like to make sure the wireframes are set to match the native functionality of NiceGUI as much as possible, so we do not build custom components/controls or define interactions that aren't supported by NiceGUI by default.

We should stay within what comes out of the box with NiceGUI, so let's clean up the wireframes to keep the overall functionality, but leverage all the native constructs of the NiceGUI framework.




== UI specification document Creation Assistance =====

Let's create first a new spec: /spec/5-web-app.md which will outline the basics: how it's deployed, which UI framework it's using, which authentication it's using (and we will go with Azure Container Apps Easy Auth).

Let's also indicate in the spec that we should be able to run the app locally, it will use UV for environment setup. Add instructions in the specs to run local for quick iterative development.

NOTE: we will assume we also run the MCP servers locally when doing web app local dev. Make sure these MCP servers can run on ports that don't conflict with each other. Propose a way to quickly run the web app local with local MCP servers.

These MCP servers may rely on AI Search, which will stay in Azure only even during local dev.

The deployment should be documented as well (we will rely on azd, and just specify what to run to deploy and test in Azure.)

Write a spec to surface that, so that the implementation GitHub Issue can be rewritten to be clearer.




== github ISSUE for UI implementation =====

ok, now based on that spec, let's write a detailed GITHUB ISSUE with all the details needed for a Github agent to implement this completely.

We want to focus on quality and simplcity to get a first cut out the door and test it, so the agent should try to keep things simple and consider putting aside difficult parts or things that need to be clarified. I would prefer to see something skipped and put into a TODO item that guessing and over-engineering.

Let's keep things simple, to do a first cut and test it out.

Add to the comments section any additional prompt guidance for the agent.