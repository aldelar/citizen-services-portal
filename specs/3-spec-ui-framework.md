# UI Framework Research & Recommendation

This document provides the research findings and recommendation for selecting a Python-friendly UI framework for the Citizen Services Portal demo application.

---

## TL;DR Recommendation

**Primary Recommendation: NiceGUI**

For the Citizen Services Portal demo application, **NiceGUI** is the recommended framework due to:
- Native 3-panel layout support with `ui.left_drawer`, `ui.row()`, `ui.column()`
- Built-in chat components (`ui.chat_message`) with avatars and timestamps
- Pure Python API with Vue.js/Quasar styling (no CSS work needed)
- FastAPI backend integration (matches existing MCP server architecture)
- Fastest time-to-prototype for multi-panel chat applications

**Alternative: Gradio** - If ML model integration becomes priority or Hugging Face deployment is desired.

---

## Requirements Summary

| Requirement | Weight | Description |
|-------------|--------|-------------|
| Multi-panel layout | High | Left sidebar + center chat + right diagram panel |
| Chat components | High | Message bubbles, input, streaming support |
| Python-native | High | Pure Python, minimal JS/CSS required |
| Rich visuals | Medium | Diagrams, charts, data visualization |
| Dev speed | Medium | Fast prototype development |
| Good defaults | Low | Minimal styling work needed |

---

## Comparison Matrix

| Framework | Chat Support | Layout Flexibility | Dev Speed | Python-Native | Overall Score |
|-----------|:------------:|:------------------:|:---------:|:-------------:|:-------------:|
| **NiceGUI** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **20/20** |
| **Gradio** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **19/20** |
| **Panel** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **18/20** |
| **Streamlit** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **17/20** |
| **Taipy** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **16/20** |
| **Solara** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | **15/20** |
| **Reflex** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | **14/20** |

### Scoring Criteria

- **Chat Support (1-5)**: Native chat widgets, streaming, message history, avatars
- **Layout Flexibility (1-5)**: 3-panel layout achievable, collapsible sidebars, resizable panels
- **Dev Speed (1-5)**: Time from zero to working prototype
- **Python-Native (1-5)**: Pure Python or requires JS/React knowledge

---

## Top 3 Candidates: Detailed Analysis

### 1. NiceGUI ⭐ Recommended

**Pros:**
- ✅ Native `ui.left_drawer` for collapsible sidebar
- ✅ Built-in `ui.chat_message` component with avatars, timestamps, sent/received styling
- ✅ Vue.js/Quasar styling provides modern, polished UI out of the box
- ✅ FastAPI backend (aligns with existing MCP server architecture)
- ✅ Real-time event-driven updates via websockets
- ✅ Flexible row/column layouts for multi-panel design
- ✅ Active development and good documentation

**Cons:**
- ❌ Smaller community than Streamlit/Gradio
- ❌ No native Jupyter integration (not needed for demo)
- ❌ Less ML-specific features (not needed for this use case)

**3-Panel Layout Example:**

```python
from nicegui import ui

# Left Sidebar - Project Selection (collapsible)
with ui.left_drawer().classes('bg-blue-50') as drawer:
    ui.label('Projects').classes('text-h6')
    with ui.list():
        ui.item('Building Permits', on_click=lambda: ui.notify('Selected'))
        ui.item('Utility Services')
        ui.item('Property Tax')

# Header with drawer toggle
with ui.header().classes('bg-blue-600 text-white'):
    ui.button(icon='menu', on_click=drawer.toggle).props('flat')
    ui.label('Citizen Services Portal').classes('text-h5')

# Main content with center chat and right diagram panel
with ui.row().classes('w-full h-screen'):
    # Center - Chat Interface
    with ui.column().classes('w-2/3 p-4'):
        ui.label('Chat with AI Assistant').classes('text-h6')
        with ui.column().classes('border rounded p-4 h-96 overflow-auto'):
            ui.chat_message('Hello! How can I help you today?',
                          name='Assistant', stamp='10:30 AM', avatar='🤖')
            ui.chat_message('I need help with a building permit',
                          name='You', stamp='10:31 AM', sent=True)
        ui.input('Type your message...').classes('w-full')
    
    # Right - Project Diagram/Overview
    with ui.column().classes('w-1/3 p-4 bg-gray-50'):
        ui.label('Project Overview').classes('text-h6')
        ui.mermaid('''
        graph TD
            A[Submit Application] --> B[Review]
            B --> C[Approval]
            C --> D[Permit Issued]
        ''')

ui.run()
```

---

### 2. Gradio

**Pros:**
- ✅ Excellent native `gr.Chatbot` component with streaming support
- ✅ Built-in `gr.Sidebar` component (collapsible, left or right)
- ✅ Blocks API for flexible layouts (`gr.Row`, `gr.Column`)
- ✅ One-click Hugging Face Spaces deployment
- ✅ Very low code for quick demos
- ✅ Large ML/AI community

**Cons:**
- ❌ Less flexible for complex custom layouts
- ❌ Template-like feel may limit customization
- ❌ Better suited for ML model demos than full applications

**3-Panel Layout Example:**

```python
import gradio as gr

def respond(message, history):
    return f"You asked about: {message}"

with gr.Blocks(fill_height=True) as demo:
    with gr.Row():
        # Left Sidebar - Project Selection
        with gr.Sidebar():
            gr.Markdown("## Projects")
            gr.Radio(
                ["Building Permits", "Utility Services", "Property Tax"],
                label="Select Project"
            )
        
        # Center - Chat Interface
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="AI Assistant", scale=1)
            msg = gr.Textbox(placeholder="Type your message...")
            msg.submit(respond, [msg, chatbot], chatbot)
        
        # Right - Project Diagram
        with gr.Column(scale=1):
            gr.Markdown("## Project Overview")
            gr.Image("diagram.png", label="Process Flow")

demo.launch()
```

---

### 3. Panel (HoloViz)

**Pros:**
- ✅ Excellent `ChatInterface` and `ChatFeed` components
- ✅ Built-in templates with sidebar support (`FastListTemplate`, etc.)
- ✅ Strong data visualization ecosystem integration
- ✅ Streaming support for LLM responses
- ✅ Large, mature community
- ✅ Works in Jupyter and standalone

**Cons:**
- ❌ Steeper learning curve than NiceGUI/Gradio
- ❌ More data science focused, less general web app feel
- ❌ Template-based layouts may feel constrained

**3-Panel Layout Example:**

```python
import panel as pn

pn.extension()

# Define components
sidebar = pn.Column(
    pn.pane.Markdown("## Projects"),
    pn.widgets.RadioButtonGroup(
        options=['Building Permits', 'Utility Services', 'Property Tax']
    ),
    width=200
)

def respond(contents, user, instance):
    return f"You asked about: {contents}"

chat = pn.chat.ChatInterface(
    callback=respond,
    placeholder="Type your message..."
)

diagram = pn.Column(
    pn.pane.Markdown("## Project Overview"),
    pn.pane.Markdown("""
    ```mermaid
    graph TD
        A[Submit] --> B[Review]
        B --> C[Approve]
    ```
    """)
)

# Combine in template
template = pn.template.FastListTemplate(
    title="Citizen Services Portal",
    sidebar=[sidebar],
    main=[pn.Row(chat, diagram)]
)

template.servable()
```

---

## Other Frameworks Evaluated

### Streamlit

**Why Not Recommended:**
- Multi-panel layouts require workarounds (columns don't resize well)
- Right-side panels are awkward to implement
- Chat components added recently but less mature
- Execution model (re-run on interaction) complicates state management

### Taipy

**Why Not Recommended:**
- More enterprise-focused with heavier learning curve
- Menu/sidebar navigation is page-based, not panel-based
- Better for data pipelines than chat interfaces
- Overkill for a demo application

### Solara

**Why Not Recommended:**
- Smaller community and fewer examples
- React-style thinking required
- Chat components are in "lab" (experimental) status
- Better for Jupyter-first workflows

### Reflex

**Why Not Recommended:**
- Requires React/frontend thinking despite Python syntax
- Steeper learning curve for pure Python developers
- More suited for full web applications, not demos
- Longer time to first prototype

---

## Open Questions for Stakeholder Input

1. **Deployment Target**: Where will the demo be hosted?
   - If Hugging Face Spaces → Consider Gradio
   - If Azure Container Apps → NiceGUI (FastAPI-based) is ideal
   - If Jupyter notebooks → Consider Panel

2. **Real-time Collaboration**: Do multiple users need to see the same chat?
   - If yes → NiceGUI or Panel (built-in websocket support)
   - If no → Any framework works

3. **Integration with Existing Infrastructure**: 
   - MCP servers use FastAPI → NiceGUI uses FastAPI backend (natural fit)
   - Cosmos DB for memory → All frameworks can integrate via Python SDK

4. **Future Production Use**: Is this demo a precursor to production?
   - If yes → Consider Reflex or Panel for scalability
   - If no → NiceGUI is fastest for demo purposes

5. **Visualization Complexity**: What diagrams are needed?
   - Simple flowcharts → Any framework (Mermaid support)
   - Complex interactive charts → Panel or Streamlit
   - Custom SVG/Canvas → NiceGUI (supports custom elements)

---

## Recommendation Summary

| Priority | Framework | When to Choose |
|----------|-----------|----------------|
| **Primary** | NiceGUI | Default choice for this demo |
| **Alternative 1** | Gradio | If Hugging Face deployment or simpler ML demo is preferred |
| **Alternative 2** | Panel | If complex data visualization is added later |

---

## Next Steps

1. **Validate with 30-minute spike** (optional):
   - Build the 3-panel layout in NiceGUI using the example code above
   - Verify Mermaid diagram rendering works for project overview

2. **Create demo application scaffold**:
   - Set up NiceGUI project in `src/web/portal/`
   - Integrate with existing Cosmos DB for chat history
   - Connect to LADBS/LADWP AI agents via API

3. **Iterate on UI/UX**:
   - Implement collapsible left sidebar for project selection
   - Add streaming chat responses from AI agents
   - Create project diagram visualizations for right panel

---

## References

- [NiceGUI Documentation](https://nicegui.io/documentation)
- [NiceGUI Chat App Example](https://github.com/zauberzeug/nicegui/blob/main/examples/chat_app/main.py)
- [Gradio Documentation](https://www.gradio.app/docs)
- [Panel Chat Interface Guide](https://panel.holoviz.org/how_to/streamlit_migration/chat.html)
- [Streamlit Chat Components](https://docs.streamlit.io/develop/api-reference/chat)
