const messages = {
  common: {
    language: 'Language',
    theme: {
      label: 'Theme',
      light: 'Light',
      dark: 'Dark',
    },
  },
  auth: {
    productTagline: 'Building Energy Management Intelligence Platform',
    teamOrigin: 'CPNS, Beijing University of Technology',
    cpnsUrl: 'https://cpns.bjut.edu.cn/index.html',
    cpnsLabel: 'CPNS Website',
    copyright: '© 2026 BEM-Nexus Authors. All rights reserved.',
    login: {
      title: 'Administrator Login',
      subtitle: 'Enter the BEM-Nexus workspace with the administrator account.',
      failure: 'Sign in failed.',
    },
    setup: {
      title: 'Initial Setup',
      subtitle: 'Create the single administrator account for this deployment.',
      passwordHint: 'At least 10 characters.',
      failure: 'Setup failed.',
    },
    fields: {
      setupToken: 'Setup Token',
      username: 'Username',
      usernameHint: '1-128 characters; leading and trailing spaces are ignored.',
      password: 'Password',
      confirmPassword: 'Confirm Password',
    },
    actions: {
      createAdmin: 'Create Administrator',
      creating: 'Creating...',
      signIn: 'Sign In',
      verifying: 'Verifying...',
    },
  },
  shell: {
    subtitle: 'Simulation Intelligence',
    loading: 'Loading Workspace...',
    accountFallback: 'Account',
    pages: {
      home: 'Home Page',
      visualization: 'Visualization',
      chat: 'Chat Agent',
      llmSettings: 'LLM Settings',
      knowledgeBase: 'Knowledge Base',
      toolSystem: 'Tool System',
      help: 'Help Center',
    },
    titles: {
      home: 'Building Energy Management - Nexus',
      visualization: 'Visualization',
      chat: 'Chat Agent',
      llmSettings: 'LLM Settings',
      knowledgeBase: 'Knowledge Base',
      toolSystem: 'Tool System',
      help: 'Help Center',
    },
    actions: {
      collapse: 'Collapse',
      theme: 'Theme',
      logout: 'Logout',
    },
  },
  home: {
    title: 'Welcome to BEM-Nexus',
    subtitle:
      'A next-generation building energy simulation platform, combining interactive visualization and AI-driven automation.',
    explore: 'Explore',
    modules: {
      visualization: {
        title: 'Visualization',
        description:
          'Experience real-time building energy simulation with interactive 3D rendering and 2D floor thermal maps. Fully customizable with your own IDF/EPW files and simulation parameters.',
        features: [
          '⚡ Real-time energy simulation streaming',
          '🏢 Interactive 3D building rendering',
          '🌡️ 2D floor thermal heatmaps',
          '⚙️ Custom IDF, EPW & parameters',
        ],
      },
      chat: {
        title: 'Chat Agent',
        description:
          'An intelligent assistant powered by multi-model LLMs. It automates EnergyPlus workflows, develops MCP tools, analyzes simulation results, and leverages powerful context memory.',
        features: [
          '🤖 Multi-model LLM natural language UI',
          '🛠️ EnergyPlus MCP tool development',
          '📊 Automated simulation result analysis',
          '🧠 Powerful context & memory engineering',
        ],
      },
      llmSettings: {
        title: 'LLM Settings',
        description:
          'Configure Claude, OpenAI, and OpenAI-compatible providers for DashScope, DeepSeek, GLM, local gateways, and other model endpoints.',
        features: [
          '🔑 Reference-only credential storage',
          '🧪 Connection test status',
          '🧩 Claude, OpenAI & compatible APIs',
          '✅ Chat-ready usable model filter',
        ],
      },
      knowledgeBase: {
        title: 'Knowledge Base',
        description:
          'Upload engineering references, index them with Qwen text-embedding-v4, test retrieval, and preview citations for Chat Agent answers.',
        features: [
          '📄 Document upload and indexing',
          '🧠 Qwen API embedding configuration',
          '🔎 Local KB and web source controls',
          '🔖 Citation preview',
        ],
      },
      toolSystem: {
        title: 'Tool System',
        description:
          'Understand the governed Agent tool platform: MCP adapters, EnergyPlus tools, Python sandbox execution, workspace tools, traces, artifacts, and confirmation boundaries.',
        features: [
          '🧰 MCP and backend tool registry',
          '⚙️ EnergyPlus resource tools',
          '🧪 Python sandbox fallback',
          '🛡️ Trace, artifacts and safety gates',
        ],
      },
      help: {
        title: 'Help Center',
        description:
          'Your central hub for platform documentation, quick start guides, and contact information for troubleshooting.',
        features: [
          '🚀 Quick start guides',
          '📖 Comprehensive platform docs',
          '🛟 Troubleshooting & contact support',
        ],
      },
    },
  },
  knowledge: {
    kicker: 'Knowledge Base',
    title: 'RAG Sources',
    refresh: 'Refresh',
    library: 'Library',
    name: 'Name',
    embeddingModel: 'Embedding Model',
    description: 'Description',
    create: 'Create',
    delete: 'Delete',
    documents: 'Documents',
    upload: 'Upload',
    reindex: 'Reindex',
    chunkList: 'Chunk List',
    noDocument: 'No document selected',
    noChunks: 'No chunks available for the selected document.',
    searchTest: 'Search Test',
    query: 'Query',
    localKb: 'Local KB',
    webSearch: 'Web Search',
    search: 'Search',
    retrievedChunks: 'Retrieved Chunks',
    requiresReindex: 'Requires Reindex',
    docs: 'Docs',
    chunks: 'Chunks',
    dims: 'dims',
    prompts: {
      missingEmbedding: 'Configure Qwen Embedding Settings to index and search Knowledge Base documents.',
      requiresReindex: 'Reindex this library with Qwen text-embedding-v4 before searching.',
    },
    status: {
      loaded: 'Knowledge Base metadata loaded.',
      created: 'Knowledge Base created.',
      deleted: 'Knowledge Base deleted.',
      processed: 'Document processed.',
      reindexed: 'Reindex request completed.',
      retrieved: 'Retrieved {count} source chunks.',
    },
    failures: {
      load: 'Failed to load Knowledge Base.',
      create: 'Failed to create Knowledge Base.',
      delete: 'Failed to delete Knowledge Base.',
      process: 'Document processing failed.',
      reindex: 'Reindex failed.',
      search: 'Search failed.',
    },
  },
  llmSettings: {
    hero: {
      title: 'Provider Workspace',
      description: 'Provider credentials, model names, capabilities, and connection status.',
    },
    actions: {
      refresh: 'Refresh',
      save: 'Save',
      saving: 'Saving...',
      add: 'Add',
      cancel: 'Cancel',
      customProvider: 'Custom Provider',
    },
    metrics: {
      enabledProviders: 'Enabled Providers',
      usableChatModels: 'Usable Chat Models',
      credentialExposure: 'Credential Exposure',
      referenceOnly: 'Reference Only',
    },
    sections: {
      providerPresets: 'Provider Presets',
      providerPresetsDescription: 'Start from official endpoint patterns, then adjust credentials or model names.',
      custom: 'Custom',
      providers: 'Providers',
      models: 'Models',
      loading: 'Loading LLM Settings...',
    },
    recentAuth: {
      label: 'Confirm Administrator Password',
      placeholder: 'Required for credential changes',
      actions: {
        confirmProviderTest: 'Confirm And Test Provider',
        confirmModelTest: 'Confirm And Test Model',
        confirmEmbeddingTest: 'Confirm And Test Embeddings',
        confirmEmbeddingSave: 'Confirm And Save Embedding Key',
        confirmWebSearchTest: 'Confirm And Test External Search',
        confirmWebSearchSave: 'Confirm And Save External Search',
        confirmSave: 'Confirm And Save',
        confirming: 'Confirming...',
      },
    },
    embedding: {
      title: 'Embedding Settings',
      description: 'Configure Qwen Embedding Settings to index and search Knowledge Base documents.',
      provider: 'Provider',
      model: 'Model',
      dimension: 'Dimension',
      apiKey: 'API Key',
      placeholder: 'Enter or update the Qwen embedding key',
      saveKey: 'Save Key',
      test: 'Test',
      clear: 'Clear',
    },
    status: {
      saved: 'Saved',
      notConfigured: 'Not configured',
      testing: 'Testing',
      testingProgress: 'Testing...',
      usable: 'Usable',
      failed: 'Failed',
      untested: 'Untested',
      connectionFailed: 'Connection failed',
    },
    provider: {
      fallbackName: 'Provider',
      modelCount: '{count} Models',
      noCredentialReference: 'No Credential Reference',
      noBaseUrl: 'No Base URL',
      fields: {
        providerId: 'Provider ID',
        providerLabel: 'Provider Label',
        providerFamily: 'Provider Family',
        timeout: 'Timeout',
        baseUrl: 'Base URL',
        apiKeyReference: 'API Key Reference',
        apiKey: 'API Key',
      },
      placeholders: {
        storedPrivately: 'Stored privately on save',
      },
      hints: {
        credentialConfigured: 'Credential configured. Enter a new key only to rotate it.',
      },
      actions: {
        test: 'Test Provider',
        remove: 'Remove Provider',
      },
      enabled: 'Enabled',
    },
    model: {
      fields: {
        internalId: 'Internal ID',
        provider: 'Provider',
        displayName: 'Display Name',
        providerModelName: 'Provider Model Name',
        temperature: 'Temperature',
      },
      flags: {
        enabled: 'Enabled',
        chat: 'Chat',
        reasoning: 'Reasoning',
        thinkingBody: 'Thinking Body',
      },
      status: {
        lastTest: 'Last Test: {time}',
        notTested: 'Connection has not been tested.',
      },
      actions: {
        test: 'Test Connection',
        remove: 'Remove Model',
      },
    },
    notices: {
      saved: 'Settings saved. Raw keys were removed from the response state.',
      embeddingCleared: 'Embedding key cleared.',
      embeddingSaved: 'Embedding key saved. Raw keys were removed from the response state.',
      embeddingUsable: 'Embedding connection is usable.',
      embeddingSanitizedFailure: 'Embedding test completed with a sanitized failure.',
      providerAlreadyExists: '{name} is already in Providers.',
      providerAdded: '{name} provider added. Add models manually after testing the provider.',
      customProviderAdded: 'Custom provider added. Rename it below if needed.',
      providerUsable: 'Provider connection is usable.',
      providerSanitizedFailure: 'Provider test completed with a sanitized failure.',
      modelUsable: 'Connection is usable.',
      modelSanitizedFailure: 'Connection test completed with a sanitized failure.',
    },
    failures: {
      load: 'Failed to load LLM Settings.',
      save: 'Failed to save LLM Settings.',
      saveEmbedding: 'Failed to save Embedding Settings.',
      testEmbedding: 'Embedding Settings test failed.',
      passwordRequired: 'Password confirmation is required to save provider credentials.',
      passwordConfirmation: 'Password confirmation failed.',
      addProviderFirst: 'Add a provider before adding a model.',
      providerTest: 'Provider connection test failed.',
      selectValidModel: 'Select a valid model before testing the connection.',
      selectValidProvider: 'Select a valid provider before testing the model.',
      modelTest: 'Connection test failed.',
    },
  },
  search: {
    webSettings: {
      title: 'External Search Settings',
      description: 'Configure a SearXNG-compatible JSON endpoint for Chat Agent web evidence.',
      enabled: 'Enabled',
      provider: 'Provider',
      baseUrl: 'Base URL',
      apiKey: 'API Key',
      placeholder: 'Optional saved search key',
      timeout: 'Timeout (s)',
      maxResults: 'Max Results',
      save: 'Save Search',
      test: 'Test Search',
      clear: 'Clear Key',
      status: {
        disabled: 'Disabled',
        unconfigured: 'Unconfigured',
      },
      notices: {
        saved: 'External search settings saved.',
        cleared: 'External search key cleared.',
        usable: 'External search provider is usable.',
        sanitizedFailure: 'External search test completed with a sanitized failure.',
      },
      failures: {
        save: 'Failed to save External Search Settings.',
        test: 'External Search Settings test failed.',
      },
    },
  },
  viewer3d: {
    common: {
      close: 'Close',
    },
    toolbar: {
      settings: 'Settings',
      visibility: 'Show / Hide',
      exportImage: 'Export Image',
      help: 'Help',
      fullscreen: 'Fullscreen',
      exitFullscreen: 'Exit Fullscreen',
    },
    command: {
      placeholder: "Type '/' then enter command (help / shadowalt / animatecamera 36 cw ...)",
    },
    actions: {
      reset: 'Reset',
    },
    notices: {
      settingsCopied: 'Settings copied to clipboard.',
      settingsApplied: 'Settings applied.',
      invalidSettings: 'Invalid settings format in clipboard.',
    },
    visibility: {
      title: 'Show / Hide',
      filterBy: 'Filter By',
      zones: 'Zones',
      height: 'Height',
      both: 'Both',
      showAll: 'Show All',
      hideAll: 'Hide All',
      heightRange: 'Height Range',
      min: 'Min',
      max: 'Max',
    },
    settings: {
      title: 'Settings',
      visual: 'Visual',
      shading: 'Shading',
      edgeThickness: 'Edge Thickness',
      hiddenObjects: 'Hidden Objects',
      hiddenModes: {
        hide: 'Hide',
        wire: 'Wire',
        ghost: 'Ghost',
      },
      shadow: 'Shadow',
      transparency: 'Transparency',
      debug: 'Debug',
      navigationSensitivity: 'Navigation Sensitivity',
      materialsBy: 'Materials By',
      surfaceType: 'Surface Type',
      construction: 'Construction',
      windowOpacity: 'Window Opacity',
      shadows: 'Shadows',
      selfShadow: 'Self Shadow',
      altitude: 'Altitude',
      azimuth: 'Azimuth',
      height: 'Height',
    },
    help: {
      title: 'Help',
      sections: {
        scope: {
          title: 'Viewer Scope',
          body: 'Inspect parsed IDF geometry, filter surfaces, adjust materials, and export the current viewport.',
        },
        toolbar: {
          title: 'Toolbar',
          settings: 'Settings: material, edge, transparency, and shadow controls.',
          visibility: 'Show / Hide: zone and height range visibility filters.',
          exportImage: 'Export Image: save the current viewport as a PNG.',
          help: 'Help: open this reference panel.',
          fullscreen: 'Fullscreen: enter or exit the fullscreen viewer.',
        },
        mouse: {
          title: 'Mouse',
          left: 'Left Mouse: rotate the model.',
          shiftLeft: 'Shift + Left Mouse: snap the camera angle.',
          pan: 'Right or Middle Mouse: pan the view.',
          wheel: 'Wheel: zoom in or out.',
        },
        keyboard: {
          title: 'Keyboard',
          reset: 'R: reset the camera.',
          exportImage: 'S: export the current viewport image.',
          command: '/: open the command prompt.',
          copy: 'Ctrl + Shift + C: copy viewport settings.',
          paste: 'Ctrl + Shift + V: paste viewport settings.',
        },
        command: {
          title: 'Command Prompt',
          help: 'help: open the Help panel.',
          shadowAlt: 'shadowalt 45: set shadow altitude.',
          shadowAzm: 'shadowazm 90: set shadow azimuth.',
          selfShadow: 'selfshadow on/off: toggle self-shadowing.',
          cameraFov: 'camerafov 30: set the camera field of view.',
        },
      },
    },
  },
  visualization: {
    emptySelection: 'Select a module from the sidebar to get started.',
    fields: {
      idfFile: 'Building File (IDF)',
      epwFile: 'Weather File (EPW)',
      environmentName: 'Environment Name',
      timestepsPerHour: 'Timesteps per Hour (1-6)',
      runStartDate: 'Run Start Date',
      runEndDate: 'Run End Date',
      controlMode: 'Control Mode',
      sessionId: 'Session ID',
    },
    file: {
      choose: 'Choose File',
      none: 'No file chosen',
      notCreated: 'Not created',
    },
    actions: {
      parseConfiguration: 'Parse Configuration',
      parsing: 'Parsing...',
      saveConfiguration: 'Save Configuration',
      saving: 'Saving...',
      startSimulation: 'Start Simulation',
      stopSimulation: 'Stop Simulation',
      refreshRuntime: 'Refresh Runtime',
      confirmObservations: 'Confirm Observations',
      observationsConfirmed: 'Observations Confirmed',
      confirmMeters: 'Confirm Meters',
      metersConfirmed: 'Meters Confirmed',
      confirmActuators: 'Confirm Actuators',
      actuatorsConfirmed: 'Actuators Confirmed',
    },
    stream: {
      realtime: 'Realtime',
      batch: 'Batch',
    },
    sections: {
      observationVariables: 'Observation Variables',
      outdoorVariables: 'Outdoor Variables',
      indoorZoneVariables: 'Indoor Zone Variables',
      energyMeters: 'Energy Meters',
      actuators: 'Actuators',
      chartWindow: 'Chart Window',
      all: 'All',
      exportSet: 'Export Set',
    },
    calendar: {
      openStart: 'Open Start Date Calendar',
      openEnd: 'Open End Date Calendar',
    },
  },
  help: {
    status: {
      availableNow: 'Available Now',
    },
    hero: {
      kicker: 'BEM-Nexus Guide',
      title: 'Product Help Center',
      description:
        'A practical map of the current BEM-Nexus workspace: simulation, Chat Agent, LLM Settings, Knowledge Base, Tool System, security, and export workflows.',
      readyTitle: 'Available Now',
      readyDescription:
        'Simulation, Chat Agent, Knowledge Base, Tool System, secure login, reports, and deployment-ready workspace persistence.',
      tags: {
        simulation: 'Simulation',
        agent: 'Agent',
        knowledge: 'Knowledge',
        tools: 'Tools',
      },
    },
    sections: {
      workflow: 'Workflow Guide',
      workflowDescription: 'Use this order for stable daily analysis.',
      moduleDirectory: 'Which Module To Use',
      moduleDirectoryDescription: 'Map each product capability to the module that owns it.',
      featureGuide: 'Feature Guide',
      featureDescription: 'Quick references for the surfaces used most often.',
      toolSystem: 'Tool System Boundaries',
      toolSystemDescription: 'Use tools for resource-backed actions, sandboxed execution, and traceable artifacts.',
      currentGuides: 'Current Operation Guides',
      currentGuidesDescription: 'Stable behavior available in the current product.',
      operatingNotes: 'Operating Notes',
      operatingDescription: 'Short reminders for reliable use.',
    },
    capabilities: {
      simulation: {
        title: 'Simulation',
        summary:
          'Prepare EnergyPlus inputs, confirm requested outputs, run studies, and inspect charts, maps, geometry, logs, and export packages from one workspace.',
        points: {
          idfWorkflow: 'IDF and EPW workflow',
          liveState: 'Live run state and charts',
          exports: '2D, 3D, log, and package exports',
        },
      },
      chat: {
        title: 'Chat Agent',
        summary:
          'Ask model-backed questions, inspect the agent thought chain, call approved MCP tools, monitor context budget, and export the selected answer report.',
        points: {
          markdown: 'Markdown and formula rendering',
          trace: 'Trace and context visibility',
          report: 'Selected-session report export',
        },
      },
      llmSettings: {
        title: 'LLM Settings',
        summary:
          'Configure providers and models from the UI, validate connectivity, control usable chat models, and keep raw credentials out of normal responses.',
        points: {
          records: 'Provider and model records',
          tests: 'Connection tests',
          credentials: 'Credential masking and references',
        },
      },
      knowledgeBase: {
        title: 'Knowledge Base',
        summary:
          'Create source libraries, upload engineering references, index documents with Qwen embeddings, test retrieval, and preview cited source chunks.',
        points: {
          upload: 'Document upload and source libraries',
          indexing: 'Embedding-backed indexing and reindexing',
          citations: 'Citation preview for grounded answers',
        },
      },
      toolSystem: {
        title: 'Tool System',
        summary:
          'Inspect the governed tool boundary for EnergyPlus operations, MCP adapters, Python sandbox execution, workspace files, render contracts, and trace output.',
        points: {
          registry: 'Canonical tool registry and profiles',
          sandbox: 'Python sandbox and workspace limits',
          trace: 'Tool trace, render, and artifact contracts',
        },
      },
      secureWorkspace: {
        title: 'Secure Workspace',
        summary:
          'Use a single-admin setup flow, HttpOnly browser sessions, protected API routes, and workspace persistence for deployment-oriented operation.',
        points: {
          setupToken: 'Initial setup token',
          recentAuth: 'Recent-auth checks',
          databaseSettings: 'Database-backed settings',
        },
      },
    },
    moduleDirectory: {
      labels: {
        capability: 'Capability Needed',
        module: 'Use Module',
        useWhen: 'Use When',
      },
      home: {
        title: 'Home',
        capability: 'Find the six main work surfaces and their status.',
        module: 'Home Page',
        useWhen: 'Start a session or decide where a task belongs.',
      },
      visualization: {
        title: 'Visualization',
        capability: 'Prepare and run EnergyPlus simulations with charts, maps, and geometry.',
        module: 'Visualization',
        useWhen: 'You have IDF/EPW resources and want direct simulation operation.',
      },
      chatAgent: {
        title: 'Chat Agent',
        capability: 'Ask model-backed questions, run governed tools, and export selected answers.',
        module: 'Chat Agent',
        useWhen: 'You need natural-language analysis or tool-backed automation.',
      },
      llmSettings: {
        title: 'LLM Settings',
        capability: 'Configure chat, reasoning, embeddings, and external search providers.',
        module: 'LLM Settings',
        useWhen: 'A model, embedding, or web evidence provider must be added or tested.',
      },
      knowledgeBase: {
        title: 'Knowledge Base',
        capability: 'Upload engineering references, build embeddings, and test citation retrieval.',
        module: 'Knowledge Base',
        useWhen: 'Answers need project manuals, standards, or uploaded references.',
      },
      toolSystem: {
        title: 'Tool System',
        capability: 'Understand MCP tools, Python sandbox, workspace tools, traces, and safety gates.',
        module: 'Tool System',
        useWhen: 'A task depends on tool capability, tool boundary, or artifact behavior.',
      },
      helpCenter: {
        title: 'Help Center',
        capability: 'Review the current product map and operational guidance.',
        module: 'Help Center',
        useWhen: 'You need a quick orientation or module selection reference.',
      },
      secureWorkspace: {
        title: 'Secure Workspace',
        capability: 'Use login, recent-auth checks, protected APIs, and persisted settings.',
        module: 'Setup, Login, LLM Settings',
        useWhen: 'You are initializing a deployment or changing protected configuration.',
      },
      exports: {
        title: 'Exports And Reports',
        capability: 'Preserve simulation packages, report files, charts, logs, and artifacts.',
        module: 'Visualization, Chat Agent',
        useWhen: 'You need a saved result matching the inspected run or conversation.',
      },
      workspaceData: {
        title: 'Workspace Data',
        capability: 'Manage uploaded resources, generated artifacts, logs, and deployment state.',
        module: 'Visualization, Chat Agent, Knowledge Base',
        useWhen: 'A task depends on files already uploaded or generated in the workspace.',
      },
    },
    workflow: {
      modelSetup: {
        title: 'Set Up Models',
        text: 'Open LLM Settings first when Chat Agent, embeddings, or external evidence are not configured.',
      },
      prepare: {
        title: 'Prepare',
        text: 'Load project resources, choose the active IDF and EPW, then confirm the outputs you need before running analysis.',
      },
      analyze: {
        title: 'Analyze',
        text: 'Run simulation views and Chat Agent side by side. Keep trace, context, and tool states visible when answers depend on runtime data.',
      },
      toolReview: {
        title: 'Review Tools',
        text: 'Check Tool System and MCP status when an answer needs EnergyPlus tools, workspace files, or Python sandbox execution.',
      },
      export: {
        title: 'Export',
        text: 'Export from the module that owns the result: Simulation for run packages, Chat Agent for selected answer reports.',
      },
      preserve: {
        title: 'Preserve',
        text: 'Keep generated files, reports, logs, database records, and uploaded resources as workspace deployment assets.',
      },
    },
    features: {
      energyPlusTools: {
        title: 'EnergyPlus Tools',
        text: 'MCP tools expose model editing, output discovery, schedule changes, and runtime checks with clear ready or blocked states.',
      },
      knowledgeBase: {
        title: 'Knowledge Base',
        text: 'Use source libraries for manuals, standards, simulation notes, and citations that support Chat Agent answers.',
      },
      toolSystem: {
        title: 'Tool System',
        text: 'Use the Tool System page to understand MCP adapters, Agent-only Python, workspace file tools, traces, artifacts, and safety gates.',
      },
      reports: {
        title: 'Reports',
        text: 'Chat reports preserve the chosen conversation answer, trace summaries, model context, and attached building files.',
      },
      workspaceData: {
        title: 'Workspace Data',
        text: 'Configuration, resources, generated reports, uploads, exports, logs, and local database files are deployment assets.',
      },
      accessControl: {
        title: 'Access Control',
        text: 'Administration is single-user focused today, with protected setup, login, session refresh, and recent-auth validation.',
      },
    },
    current: {
      modelSetup: {
        title: 'Model Setup',
        text: 'LLM Settings owns provider records, model usability, embedding keys, external search configuration, and connection tests.',
      },
      dailyOperation: {
        title: 'Daily Operation',
        text: 'Use the home page and sidebar as the module map: prepare resources, run simulations, ask Chat Agent questions, and export from the owning module.',
      },
      resourceHandling: {
        title: 'Resource Handling',
        text: 'Uploaded files, generated artifacts, reports, logs, and database records are workspace assets that remain part of the deployment state.',
      },
      toolBoundaries: {
        title: 'Tool Boundaries',
        text: 'EnergyPlus actions require matching resources, model edits use confirmation data, and sandboxed execution stays inside controlled workspaces.',
      },
      exports: {
        title: 'Exports',
        text: 'Simulation packages and Chat reports are generated from the active run or session so saved results match what the user inspected.',
      },
      helpCenter: {
        title: 'Help Center',
        text: 'Use this page as the maintained product map for existing modules, capability ownership, and stable operation boundaries.',
      },
    },
    toolSystemNotes: [
      'Tool routes are selected from current-turn evidence, selected resources, and tool profile metadata.',
      'Python execution is Agent-only and fallback-oriented, with import checks, runtime limits, and workspace artifact collection.',
      'Product-display tools, Agent-only tools, internal support tools, and debug tools have separate visibility boundaries.',
    ],
    operatingNotes: [
      'Set up at least one usable chat model before using Chat Agent.',
      'Treat the workspace database and resource folders as persistent deployment data.',
      'Use the MCP tool state badges before relying on tool-backed answers.',
      'Export reports from the active session or run you want to preserve.',
    ],
  },
  toolSystem: {
    hero: {
      kicker: 'Agent Tool Platform',
      title: 'Tool System',
      description:
        'The Tool System is the governed execution layer behind Chat Agent actions. It keeps MCP adapters, EnergyPlus domain tools, Python sandbox execution, workspace file operations, render contracts, artifacts, traces, and confirmation rules under one explicit boundary.',
      boundaryTitle: 'Bounded Execution',
      boundaryDescription:
        'Tools run only when current task evidence, selected resources, schema requirements, and safety policy all line up.',
      tags: {
        mcp: 'MCP',
        energyPlus: 'EnergyPlus',
        python: 'Python',
        workspace: 'Workspace',
      },
    },
    sections: {
      platform: 'Platform Layers',
      platformDescription: 'How the Agent routes from a user task to governed tool execution.',
      catalog: 'MCP Tool Catalog',
      catalogDescription: 'Registered tools grouped by capability, with the execution boundary shown beside each tool.',
      sandbox: 'Sandbox And Workspace',
      sandboxDescription: 'General Agent tools stay separate from EnergyPlus domain tools.',
      boundaries: 'Safety Boundaries',
      boundariesDescription: 'Every tool declares its visibility, side effects, and runtime boundary.',
      workflow: 'Tool Run Lifecycle',
      workflowDescription: 'The visible trace follows route, execute, observe, and review steps.',
    },
    catalog: {
      labels: {
        capability: 'Capability',
        boundary: 'Boundary',
      },
      groups: {
        catalog: {
          title: 'Catalog And Resources',
          description: 'Registry and session-resource helpers used before a domain tool can run.',
        },
        idfInspection: {
          title: 'IDF Inspection',
          description: 'Read uploaded model structure, object counts, schedules, and internal-load objects.',
        },
        idfModification: {
          title: 'IDF Modification And Outputs',
          description: 'Draft, validate, and apply confirmed changes to model variants and output requests.',
        },
        simulation: {
          title: 'Simulation Runtime',
          description: 'Check the EnergyPlus runtime, prepare commands, execute runs, and collect run outputs.',
        },
        resultsWeather: {
          title: 'Results And Weather',
          description: 'Read SQL outputs, build summaries, validate EPW files, and create renderable overviews.',
        },
        hvacTopology: {
          title: 'HVAC Topology',
          description: 'Extract HVAC loop structure and component parameters for diagrams and inspection.',
        },
        workspace: {
          title: 'Workspace File Tools',
          description: 'Agent-only file operations inside the session workspace, never arbitrary host paths.',
        },
        pythonSandbox: {
          title: 'Python Sandbox',
          description: 'sandbox-based Python capability for explicit fallback analysis, plotting, and artifact creation.',
        },
      },
      tools: {
        eplus_mcp_tool_catalog: {
          capability: 'Lists registered tool contracts, visibility, side effects, and confirmation policy.',
          boundary: 'Read-only product-display catalog.',
        },
        eplus_model_resolve_path: {
          capability: 'Resolves model and weather references inside the current session workspace.',
          boundary: 'Internal support; session-scoped lookup.',
        },
        eplus_model_copy_file: {
          capability: 'Copies model or weather resources to a managed workspace location.',
          boundary: 'Internal support; workspace write only.',
        },
        eplus_idf_summary: {
          capability: 'Summarizes uploaded IDF object counts and core model content.',
          boundary: 'Read-only; requires an IDF resource.',
        },
        eplus_idf_list_objects: {
          capability: 'Lists IDF object types and counts.',
          boundary: 'Read-only; requires an IDF resource.',
        },
        eplus_idf_get_objects: {
          capability: 'Returns objects and fields for one requested IDF object type.',
          boundary: 'Read-only; requires an IDF resource and object type.',
        },
        eplus_schedule_inspect: {
          capability: 'Inspects Schedule objects from the uploaded model.',
          boundary: 'Read-only; requires an IDF resource.',
        },
        eplus_people_inspect: {
          capability: 'Inspects People internal-load objects.',
          boundary: 'Read-only; requires an IDF resource.',
        },
        eplus_lights_inspect: {
          capability: 'Inspects Lights internal-load objects.',
          boundary: 'Read-only; requires an IDF resource.',
        },
        eplus_equipment_inspect: {
          capability: 'Inspects ElectricEquipment internal-load objects.',
          boundary: 'Read-only; requires an IDF resource.',
        },
        eplus_schedule_patch_draft: {
          capability: 'Drafts a Schedule:Compact value patch.',
          boundary: 'Model-modifying draft; requires confirmation.',
        },
        eplus_people_density_adjust_draft: {
          capability: 'Drafts People density adjustments for a new IDF variant.',
          boundary: 'Model-modifying draft; explicit value and confirmation required.',
        },
        eplus_internal_load_patch_draft: {
          capability: 'Drafts field changes for People, Lights, or Equipment objects.',
          boundary: 'Model-modifying draft; confirmation required.',
        },
        eplus_output_request_patch_draft: {
          capability: 'Drafts output request object changes.',
          boundary: 'Model-modifying draft; confirmation required.',
        },
        eplus_idf_apply_patch: {
          capability: 'Applies a confirmed patch to a variant IDF.',
          boundary: 'Workspace write; confirmed patch payload required.',
        },
        eplus_idf_save_variant: {
          capability: 'Saves the uploaded IDF as a managed variant file.',
          boundary: 'Workspace write; confirmation required.',
        },
        eplus_loads_modify_people: {
          capability: 'Creates People load modifications.',
          boundary: 'Model-modifying; confirmation and IDF context required.',
        },
        eplus_loads_validate_people: {
          capability: 'Validates People load changes before or after modification.',
          boundary: 'Read-only validation over IDF context.',
        },
        eplus_loads_modify_lights: {
          capability: 'Creates lighting load modifications.',
          boundary: 'Model-modifying; confirmation and IDF context required.',
        },
        eplus_loads_validate_lights: {
          capability: 'Validates lighting load changes.',
          boundary: 'Read-only validation over IDF context.',
        },
        eplus_loads_modify_equipment: {
          capability: 'Creates equipment load modifications.',
          boundary: 'Model-modifying; confirmation and IDF context required.',
        },
        eplus_loads_validate_equipment: {
          capability: 'Validates equipment load changes.',
          boundary: 'Read-only validation over IDF context.',
        },
        eplus_output_get_variables: {
          capability: 'Lists configured or available output variables.',
          boundary: 'Read-only; requires IDF context.',
        },
        eplus_output_add_variables: {
          capability: 'Adds output variable requests to the model.',
          boundary: 'Model-modifying; confirmation required.',
        },
        eplus_output_get_meters: {
          capability: 'Lists configured or available output meters.',
          boundary: 'Read-only; requires IDF context.',
        },
        eplus_output_add_meters: {
          capability: 'Adds output meter requests to the model.',
          boundary: 'Model-modifying; confirmation required.',
        },
        eplus_schedule_parse_text: {
          capability: 'Parses natural-language schedule edits into structured changes.',
          boundary: 'Internal support; no direct model write.',
        },
        eplus_schedule_apply_text: {
          capability: 'Applies a parsed schedule change to an IDF variant.',
          boundary: 'Model-modifying; confirmation required.',
        },
        eplus_runtime_check: {
          capability: 'Checks EnergyPlus executable and IDD readiness.',
          boundary: 'Read-only runtime check.',
        },
        eplus_simulation_prepare: {
          capability: 'Validates simulation inputs and command shape without running.',
          boundary: 'Workspace-scoped preparation; requires IDF and optional EPW.',
        },
        eplus_simulation_run: {
          capability: 'Runs EnergyPlus for the prepared model and weather inputs.',
          boundary: 'Simulation runtime execution; workspace outputs only.',
        },
        eplus_simulation_read_err: {
          capability: 'Reads EnergyPlus ERR output for diagnostics.',
          boundary: 'Read-only workspace output inspection.',
        },
        eplus_simulation_collect_outputs: {
          capability: 'Collects generated simulation outputs and artifacts.',
          boundary: 'Workspace read/write packaging boundary.',
        },
        eplus_simulation_server_status: {
          capability: 'Reports tool service, runtime, and session workspace status.',
          boundary: 'Read-only service status.',
        },
        eplus_sql_list_outputs: {
          capability: 'Lists available SQL output variables and meters.',
          boundary: 'Read-only SQL inspection.',
        },
        eplus_sql_extract_timeseries: {
          capability: 'Extracts SQL time-series data for selected outputs.',
          boundary: 'Read-only SQL extraction; requires output selection.',
        },
        eplus_sql_monthly_summary: {
          capability: 'Creates monthly summaries from SQL results.',
          boundary: 'Read-only analysis; structured summary output.',
        },
        eplus_results_energy_temperature_overview: {
          capability: 'Builds energy and temperature overview data from results.',
          boundary: 'Read-only result analysis.',
        },
        eplus_results_render_overview: {
          capability: 'Creates renderable chart payloads for result overview.',
          boundary: 'Read-only result rendering contract.',
        },
        eplus_epw_validate: {
          capability: 'Validates EPW weather file structure and readiness.',
          boundary: 'Read-only; requires EPW context.',
        },
        eplus_epw_summary: {
          capability: 'Summarizes EPW location, period, and weather fields.',
          boundary: 'Read-only; requires EPW context.',
        },
        eplus_epw_extract_timeseries: {
          capability: 'Extracts EPW weather time series.',
          boundary: 'Read-only extraction; requires field selection.',
        },
        eplus_epw_monthly_stats: {
          capability: 'Calculates monthly EPW weather statistics.',
          boundary: 'Read-only weather analysis.',
        },
        eplus_epw_render_weather_overview: {
          capability: 'Creates renderable weather overview charts.',
          boundary: 'Read-only weather rendering contract.',
        },
        eplus_hvac_get_topology: {
          capability: 'Extracts plant, condenser, and air-loop topology.',
          boundary: 'Read-only; returns topology graph payloads.',
        },
        eplus_hvac_get_component_parameters: {
          capability: 'Inspects HVAC component field values.',
          boundary: 'Read-only; requires IDF context.',
        },
        workspace_list_dir: {
          capability: 'Lists files and folders under the workspace root.',
          boundary: 'Agent-only; workspace read.',
        },
        workspace_read_file: {
          capability: 'Reads UTF-8 files from the workspace.',
          boundary: 'Agent-only; workspace read.',
        },
        workspace_search_text: {
          capability: 'Searches workspace text files for literal matches.',
          boundary: 'Agent-only; workspace read.',
        },
        workspace_file_metadata: {
          capability: 'Returns file size and metadata without reading content.',
          boundary: 'Agent-only; workspace read.',
        },
        workspace_write_resource: {
          capability: 'Writes text resources into the workspace.',
          boundary: 'Agent-only; workspace write with confirmation.',
        },
        workspace_copy_resource: {
          capability: 'Copies workspace files to managed workspace paths.',
          boundary: 'Agent-only; workspace write with confirmation.',
        },
        workspace_append_report_fragment: {
          capability: 'Appends text fragments to a workspace report.',
          boundary: 'Agent-only; workspace write with confirmation.',
        },
        execute_python_capability_check: {
          capability: 'Checks Python imports, plotting, eppy readiness, and artifact limits.',
          boundary: 'Agent-only diagnostic; no user-facing execution button.',
        },
        execute_python_code: {
          capability: 'Runs explicit fallback Python for analysis, repair, conversion, plots, and artifacts.',
          boundary: 'Agent-only isolated sandbox with timeout, allowlist, and workspace limits.',
        },
      },
    },
    platform: {
      kernel: {
        title: 'Tool Platform Kernel',
        text: 'A canonical registry defines each tool profile, input schema, route policy, render contract, and public result shape.',
        points: {
          profiles: 'Profile metadata drives routing and display',
          results: 'Tool results use one structured envelope',
          adapters: 'Web catalog, FastMCP, and model tool schemas share metadata',
        },
      },
      mcp: {
        title: 'MCP Adapter Surface',
        text: 'MCP remains an adapter layer for exposing compatible tool metadata while the product runtime uses the backend tool registry.',
        points: {
          catalog: 'Catalog cards show ready or blocked states',
          fastmcp: 'FastMCP compatibility is maintained for tool exposure',
          metadata: 'Audience, family, capabilities, and render types are explicit',
        },
      },
      energyPlus: {
        title: 'EnergyPlus Domain Tools',
        text: 'Uploaded IDF, EPW, SQL, and simulation outputs activate domain tools for inspection, patching, runtime checks, result parsing, and charts.',
        points: {
          idf: 'IDF inspection and confirmed patch workflows',
          epw: 'EPW validation and weather overview artifacts',
          results: 'SQL outputs, summaries, and renderable chart payloads',
        },
      },
    },
    sandbox: {
      python: {
        title: 'Python Sandbox',
        text: 'Python runs as an Agent-only fallback for explicit programmable analysis, repair, transformation, and artifact creation inside the session workspace.',
      },
      workspace: {
        title: 'Workspace File Tools',
        text: 'Workspace tools read, search, copy, write, and summarize resource files through policy-checked relative references instead of host paths.',
      },
      artifacts: {
        title: 'Artifacts And Renders',
        text: 'Generated images, tables, topology graphs, chart data, text payloads, and files return as structured render instructions and public artifacts.',
      },
    },
    flow: {
      route: {
        title: 'Route',
        text: 'The planner and router score tools from current-turn intent, available resources, schemas, preconditions, and profile metadata.',
      },
      execute: {
        title: 'Execute',
        text: 'The executor validates arguments, injects safe resource context, runs the handler, and records schema, call, result, and artifact events.',
      },
      review: {
        title: 'Review',
        text: 'The reviewer checks validation status, missing context, confirmation needs, and whether tool results are sufficient for the final answer.',
      },
    },
    safeguards: [
      'Product-display, Agent-only, internal support, and debug tools are separated before the UI renders them.',
      'Model-modifying operations require explicit values or confirmation payloads; hidden defaults are not treated as known user intent.',
      'Python imports are allowlisted and execution is bounded by session workspace, timeout, output, and artifact rules.',
      'Tool output must expose structured data, render instructions, validation, trace, artifacts, and suggested next actions.',
    ],
  },
  chat: {
    title: 'Chat Agent',
    session: {
      newTitle: 'New Session',
      recoveredTask: 'Recovered task',
      autoGeneratedTask: 'Auto generated task',
    },
    sidebar: {
      sessions: 'Sessions',
      mcpTools: 'MCP Tools',
      toolCount: '21 Tools',
      contextBudget: 'Budget',
    },
    actions: {
      newSession: 'New',
      deleteSession: 'Delete',
      renameSession: 'Rename Session',
      saveSessionTitle: 'Save Session Title',
      cancelSessionTitle: 'Cancel Rename',
      exportReport: 'Report',
      refreshModels: 'Refresh usable models',
      stop: 'Stop',
      send: 'Send',
    },
    model: {
      label: 'Model',
      noUsableModels: 'No usable LLM models. Open LLM Settings and run a successful connection test.',
      noUsableModelsOption: 'No Usable Models',
      loadFailure: 'Failed to load usable LLM models.',
      streaming: 'Streaming...',
    },
    sources: {
      knowledgeBase: 'Project Knowledge',
      knowledgeBaseReady: 'Use indexed project knowledge when it is relevant.',
      noKnowledgeBase: 'No Project Knowledge',
      webSearch: 'Web',
    },
    empty: {
      title: 'Start a conversation',
      description:
        'Ask general questions directly, or upload an IDF/EPW and send model tasks like "inspect people, then add output variables".',
    },
    composer: {
      placeholder: 'Send a message...',
    },
    attachments: {
      noIdf: 'No IDF',
      noEpw: 'No EPW',
    },
    failures: {
      exportReport: 'Export report failed.',
      renameSession: 'Rename session failed.',
      renameUnavailable: 'Send a message before renaming this session.',
      stream: 'Stream failed.',
      request: 'Request failed.',
    },
    events: {
      agentDidNotFinish: 'The agent did not finish successfully.',
      agentStopped: 'Agent stopped during {phase}: {detail}',
      modelContextLoaded: 'Model context loaded.',
      contextUpdated: 'Context updated.',
      loadedMemoryHints: 'Loaded memory hints: {hints}',
    },
    contextGauge: {
      title: 'Context Gauge',
      tokens: '{count} Tokens',
      estimatedTokens: 'Estimated {count} Tokens',
      budgetSource: {
        backend: 'Backend Budget',
        fallback: 'Fallback Estimate',
      },
      degraded: {
        title: 'Degraded Context',
        fallbackReason: 'Sliding-window fallback is active.',
      },
      states: {
        hardGuard: 'Hard Guard',
        compressing: 'Compressing',
        compressed: 'Compressed',
        warning: 'Warning',
        notice: 'Notice',
        safe: 'Safe',
      },
      sources: {
        providerUsage: 'Provider Usage',
        tokenizer: 'Tokenizer',
        characterEstimate: 'Character Estimate',
      },
      breakdown: {
        messages: 'Messages',
        system: 'System',
        thoughtChain: 'Thought Chain',
        toolPayload: 'Tool Payload',
        memory: 'Memory',
        compression: 'Compression',
        resources: 'Resources',
        providerPrompt: 'Provider Prompt',
      },
      metrics: {
        modelMax: 'Model Max',
        availableInput: 'Available Input',
        responseReserve: 'Response Reserve',
        estimateSource: 'Estimate Source',
        compressionState: 'Compression State',
        thresholds: 'Thresholds',
      },
    },
  },
}

export default messages
