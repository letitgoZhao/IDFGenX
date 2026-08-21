const messages = {
  common: {
    language: '语言',
    theme: {
      label: '主题',
      light: '亮色',
      dark: '暗色',
    },
  },
  auth: {
    productTagline: '建筑能源管理智能平台',
    teamOrigin: 'CPNS, 北京工业大学',
    cpnsUrl: 'https://cpns.bjut.edu.cn/index.html',
    cpnsLabel: 'CPNS 官网',
    copyright: '© 2026 BEM-Nexus Authors. 保留所有权利。',
    login: {
      title: '管理员登录',
      subtitle: '使用管理员账户进入 BEM-Nexus 工作空间。',
      failure: '登录失败。',
    },
    setup: {
      title: '初始设置',
      subtitle: '创建唯一管理员账户并绑定当前部署。',
      passwordHint: '至少 10 个字符。',
      failure: '设置失败。',
    },
    fields: {
      setupToken: '设置令牌',
      username: '用户名',
      usernameHint: '1-128 个字符; 首尾空格会自动忽略。',
      password: '密码',
      confirmPassword: '确认密码',
    },
    actions: {
      createAdmin: '创建管理员',
      creating: '创建中...',
      signIn: '登录',
      verifying: '验证中...',
    },
  },
  shell: {
    subtitle: 'Simulation Intelligence',
    loading: '正在加载工作空间...',
    accountFallback: '账户',
    pages: {
      home: '首页',
      visualization: '可视化',
      chat: '聊天智能体',
      llmSettings: 'LLM 设置',
      knowledgeBase: '知识库',
      toolSystem: '工具系统',
      help: '帮助中心',
    },
    titles: {
      home: '建筑能源管理 - Nexus',
      visualization: '可视化',
      chat: '聊天智能体',
      llmSettings: 'LLM 设置',
      knowledgeBase: '知识库',
      toolSystem: '工具系统',
      help: '帮助中心',
    },
    actions: {
      collapse: '收起',
      theme: '主题',
      logout: '退出登录',
    },
  },
  home: {
    title: '欢迎使用 BEM-Nexus',
    subtitle: '面向建筑能源仿真的下一代平台, 融合交互式可视化与 AI 驱动自动化。',
    explore: '进入',
    modules: {
      visualization: {
        title: '可视化',
        description:
          '使用交互式 3D 渲染和 2D 楼层热力图体验实时建筑能源仿真, 并支持自定义 IDF/EPW 文件和参数。',
        features: [
          '⚡ 实时能源仿真流',
          '🏢 交互式 3D 建筑渲染',
          '🌡️ 2D 楼层热力图',
          '⚙️ 自定义 IDF、EPW 与参数',
        ],
      },
      chat: {
        title: '聊天智能体',
        description:
          '由多模型 LLM 支持的智能助手, 可自动化 EnergyPlus 工作流、开发 MCP 工具、分析仿真结果并使用上下文记忆。',
        features: [
          '🤖 多模型自然语言交互',
          '🛠️ EnergyPlus MCP 工具开发',
          '📊 自动仿真结果分析',
          '🧠 上下文与记忆工程',
        ],
      },
      llmSettings: {
        title: 'LLM 设置',
        description:
          '配置 Claude、OpenAI 以及兼容 OpenAI 的 DashScope、DeepSeek、GLM、本地网关和其他模型端点。',
        features: [
          '🔑 引用式凭据存储',
          '🧪 连接测试状态',
          '🧩 Claude、OpenAI 与兼容 API',
          '✅ 聊天可用模型筛选',
        ],
      },
      knowledgeBase: {
        title: '知识库',
        description:
          '上传工程参考资料, 使用 Qwen text-embedding-v4 建立索引, 测试检索并为 Chat Agent 答案预览引用。',
        features: [
          '📄 文档上传与索引',
          '🧠 Qwen API 嵌入配置',
          '🔎 本地知识库与网页来源控制',
          '🔖 引用预览',
        ],
      },
      toolSystem: {
        title: '工具系统',
        description:
          '了解受治理的 Agent 工具平台: MCP 适配、EnergyPlus 工具、Python sandbox 执行、工作空间工具、trace、artifact 和确认边界。',
        features: [
          '🧰 MCP 与后端工具注册表',
          '⚙️ EnergyPlus 资源工具',
          '🧪 Python sandbox fallback',
          '🛡️ Trace、artifact 与安全门禁',
        ],
      },
      help: {
        title: '帮助中心',
        description: '平台文档、快速开始指南和排障联系方式的统一入口。',
        features: ['🚀 快速开始指南', '📖 平台功能说明', '🛟 排障与支持'],
      },
    },
  },
  knowledge: {
    kicker: '知识库',
    title: 'RAG 来源',
    refresh: '刷新',
    library: '资料库',
    name: '名称',
    embeddingModel: '嵌入模型',
    description: '描述',
    create: '创建',
    delete: '删除',
    documents: '文档',
    upload: '上传',
    reindex: '重新索引',
    chunkList: '分块列表',
    noDocument: '未选择文档',
    noChunks: '当前文档暂无分块。',
    searchTest: '检索测试',
    query: '查询',
    localKb: '本地知识库',
    webSearch: '网页检索',
    search: '检索',
    retrievedChunks: '检索分块',
    requiresReindex: '需要重新索引',
    docs: '文档',
    chunks: '分块',
    dims: '维',
    prompts: {
      missingEmbedding: '请先在 LLM 设置的嵌入设置中配置 Qwen 后再索引和检索知识库文档。',
      requiresReindex: '请先使用 Qwen text-embedding-v4 重新索引该资料库。',
    },
    status: {
      loaded: '知识库元数据已加载。',
      created: '知识库已创建。',
      deleted: '知识库已删除。',
      processed: '文档已处理。',
      reindexed: '重新索引请求已完成。',
      retrieved: '已检索 {count} 个来源分块。',
    },
    failures: {
      load: '加载知识库失败。',
      create: '创建知识库失败。',
      delete: '删除知识库失败。',
      process: '文档处理失败。',
      reindex: '重新索引失败。',
      search: '检索失败。',
    },
  },
  llmSettings: {
    hero: {
      title: '供应商工作区',
      description: '管理供应商凭据、模型名称、能力和连接状态。',
    },
    actions: {
      refresh: '刷新',
      save: '保存',
      saving: '保存中...',
      add: '添加',
      cancel: '取消',
      customProvider: '自定义供应商',
    },
    metrics: {
      enabledProviders: '已启用供应商',
      usableChatModels: '可用聊天模型',
      credentialExposure: '凭据暴露',
      referenceOnly: '仅引用',
    },
    sections: {
      providerPresets: '供应商预设',
      providerPresetsDescription: '从官方端点模式开始, 再调整凭据或模型名称。',
      custom: '自定义',
      providers: '供应商',
      models: '模型',
      loading: '正在加载 LLM 设置...',
    },
    recentAuth: {
      label: '确认管理员密码',
      placeholder: '凭据变更需要确认',
      actions: {
        confirmProviderTest: '确认并测试供应商',
        confirmModelTest: '确认并测试模型',
        confirmEmbeddingTest: '确认并测试嵌入',
        confirmEmbeddingSave: '确认并保存嵌入密钥',
        confirmWebSearchTest: '确认并测试外部检索',
        confirmWebSearchSave: '确认并保存外部检索',
        confirmSave: '确认并保存',
        confirming: '确认中...',
      },
    },
    embedding: {
      title: '嵌入设置',
      description: '配置 Qwen 嵌入设置, 用于索引和检索知识库文档。',
      provider: '供应商',
      model: '模型',
      dimension: '维度',
      apiKey: 'API 密钥',
      placeholder: '输入或更新 Qwen 嵌入密钥',
      saveKey: '保存密钥',
      test: '测试',
      clear: '清除',
    },
    status: {
      saved: '已保存',
      notConfigured: '未配置',
      testing: '测试中',
      testingProgress: '测试中...',
      usable: '可用',
      failed: '失败',
      untested: '未测试',
      connectionFailed: '连接失败',
    },
    provider: {
      fallbackName: '供应商',
      modelCount: '{count} 个模型',
      noCredentialReference: '无凭据引用',
      noBaseUrl: '无 Base URL',
      fields: {
        providerId: '供应商 ID',
        providerLabel: '供应商标签',
        providerFamily: '供应商类型',
        timeout: '超时',
        baseUrl: 'Base URL',
        apiKeyReference: 'API 密钥引用',
        apiKey: 'API 密钥',
      },
      placeholders: {
        storedPrivately: '保存后将私密存储',
      },
      hints: {
        credentialConfigured: '凭据已配置。仅在轮换时输入新密钥。',
      },
      actions: {
        test: '测试供应商',
        remove: '删除供应商',
      },
      enabled: '启用',
    },
    model: {
      fields: {
        internalId: '内部 ID',
        provider: '供应商',
        displayName: '显示名称',
        providerModelName: '供应商模型名称',
        temperature: 'Temperature',
      },
      flags: {
        enabled: '启用',
        chat: '聊天',
        reasoning: '推理',
        thinkingBody: 'Thinking Body',
      },
      status: {
        lastTest: '上次测试: {time}',
        notTested: '尚未测试连接。',
      },
      actions: {
        test: '测试连接',
        remove: '删除模型',
      },
    },
    notices: {
      saved: '设置已保存。原始密钥已从响应状态中移除。',
      embeddingCleared: '嵌入密钥已清除。',
      embeddingSaved: '嵌入密钥已保存。原始密钥已从响应状态中移除。',
      embeddingUsable: '嵌入连接可用。',
      embeddingSanitizedFailure: '嵌入测试完成, 并返回已清理的失败信息。',
      providerAlreadyExists: '{name} 已存在于供应商列表中。',
      providerAdded: '{name} 供应商已添加。测试供应商后请手动添加模型。',
      customProviderAdded: '自定义供应商已添加。如有需要请在下方重命名。',
      providerUsable: '供应商连接可用。',
      providerSanitizedFailure: '供应商测试完成, 并返回已清理的失败信息。',
      modelUsable: '连接可用。',
      modelSanitizedFailure: '连接测试完成, 并返回已清理的失败信息。',
    },
    failures: {
      load: '加载 LLM 设置失败。',
      save: '保存 LLM 设置失败。',
      saveEmbedding: '保存嵌入设置失败。',
      testEmbedding: '嵌入设置测试失败。',
      passwordRequired: '保存供应商凭据需要确认密码。',
      passwordConfirmation: '密码确认失败。',
      addProviderFirst: '添加模型前请先添加供应商。',
      providerTest: '供应商连接测试失败。',
      selectValidModel: '测试连接前请选择有效模型。',
      selectValidProvider: '测试模型前请选择有效供应商。',
      modelTest: '连接测试失败。',
    },
  },
  search: {
    webSettings: {
      title: '外部检索设置',
      description: '为 Chat Agent 网页证据配置 SearXNG-compatible JSON 端点。',
      enabled: '启用',
      provider: '供应商',
      baseUrl: 'Base URL',
      apiKey: 'API 密钥',
      placeholder: '可选的已保存检索密钥',
      timeout: '超时（秒）',
      maxResults: '最大结果数',
      save: '保存检索',
      test: '测试检索',
      clear: '清除密钥',
      status: {
        disabled: '已禁用',
        unconfigured: '未配置',
      },
      notices: {
        saved: '外部检索设置已保存。',
        cleared: '外部检索密钥已清除。',
        usable: '外部检索供应商可用。',
        sanitizedFailure: '外部检索测试完成, 并返回已清理的失败信息。',
      },
      failures: {
        save: '保存外部检索设置失败。',
        test: '外部检索设置测试失败。',
      },
    },
  },
  viewer3d: {
    common: {
      close: '关闭',
    },
    toolbar: {
      settings: '设置',
      visibility: '显示 / 隐藏',
      exportImage: '导出图片',
      help: '帮助',
      fullscreen: '全屏',
      exitFullscreen: '退出全屏',
    },
    command: {
      placeholder: "输入 '/' 后回车执行命令（help / shadowalt / animatecamera 36 cw ...）",
    },
    actions: {
      reset: '重置',
    },
    notices: {
      settingsCopied: '设置已复制到剪贴板。',
      settingsApplied: '设置已应用。',
      invalidSettings: '剪贴板中的设置格式无效。',
    },
    visibility: {
      title: '显示 / 隐藏',
      filterBy: '筛选方式',
      zones: '区域',
      height: '高度',
      both: '两者',
      showAll: '全部显示',
      hideAll: '全部隐藏',
      heightRange: '高度范围',
      min: '最小',
      max: '最大',
    },
    settings: {
      title: '设置',
      visual: '显示',
      shading: '遮阳面',
      edgeThickness: '边线粗细',
      hiddenObjects: '隐藏对象',
      hiddenModes: {
        hide: '隐藏',
        wire: '线框',
        ghost: '半透明',
      },
      shadow: '阴影',
      transparency: '透明',
      debug: '调试',
      navigationSensitivity: '导航灵敏度',
      materialsBy: '材质着色方式',
      surfaceType: '表面类型',
      construction: '构造',
      windowOpacity: '窗口透明度',
      shadows: '阴影',
      selfShadow: '自阴影',
      altitude: '高度角',
      azimuth: '方位角',
      height: '高度',
    },
    help: {
      title: '帮助',
      sections: {
        scope: {
          title: '查看器范围',
          body: '查看解析后的 IDF 几何，筛选表面，调整材质显示，并导出当前视角。',
        },
        toolbar: {
          title: '工具栏',
          settings: '设置：调整材质、边线、透明度和阴影。',
          visibility: '显示 / 隐藏：按区域或高度范围筛选可见对象。',
          exportImage: '导出图片：把当前视角保存为 PNG。',
          help: '帮助：打开当前说明面板。',
          fullscreen: '全屏：进入或退出全屏查看器。',
        },
        mouse: {
          title: '鼠标',
          left: '左键：旋转模型。',
          shiftLeft: 'Shift + 左键：吸附相机角度。',
          pan: '右键或中键：平移视图。',
          wheel: '滚轮：放大或缩小。',
        },
        keyboard: {
          title: '键盘',
          reset: 'R：重置相机。',
          exportImage: 'S：导出当前视角图片。',
          command: '/：打开命令输入框。',
          copy: 'Ctrl + Shift + C：复制视角设置。',
          paste: 'Ctrl + Shift + V：粘贴视角设置。',
        },
        command: {
          title: '命令输入',
          help: 'help：打开帮助面板。',
          shadowAlt: 'shadowalt 45：设置阴影高度角。',
          shadowAzm: 'shadowazm 90：设置阴影方位角。',
          selfShadow: 'selfshadow on/off：开启或关闭自阴影。',
          cameraFov: 'camerafov 30：设置相机视场角。',
        },
      },
    },
  },
  visualization: {
    emptySelection: '请从侧边栏选择一个模块开始。',
    fields: {
      idfFile: '建筑文件 (IDF)',
      epwFile: '天气文件 (EPW)',
      environmentName: '环境名称',
      timestepsPerHour: '每小时步数 (1-6)',
      runStartDate: '运行开始日期',
      runEndDate: '运行结束日期',
      controlMode: '控制模式',
      sessionId: '会话 ID',
    },
    file: {
      choose: '选择文件',
      none: '未选择文件',
      notCreated: '尚未创建',
    },
    actions: {
      parseConfiguration: '解析配置',
      parsing: '解析中...',
      saveConfiguration: '保存配置',
      saving: '保存中...',
      startSimulation: '开始仿真',
      stopSimulation: '停止仿真',
      refreshRuntime: '刷新运行时',
      confirmObservations: '确认观测量',
      observationsConfirmed: '观测量已确认',
      confirmMeters: '确认能耗表',
      metersConfirmed: '能耗表已确认',
      confirmActuators: '确认执行器',
      actuatorsConfirmed: '执行器已确认',
    },
    stream: {
      realtime: '实时',
      batch: '批量',
    },
    sections: {
      observationVariables: '观测变量',
      outdoorVariables: '室外变量',
      indoorZoneVariables: '室内区域变量',
      energyMeters: '能耗表',
      actuators: '执行器',
      chartWindow: '图表窗口',
      all: '全部',
      exportSet: '导出集合',
    },
    calendar: {
      openStart: '打开开始日期日历',
      openEnd: '打开结束日期日历',
    },
  },
  help: {
    status: {
      availableNow: '当前可用',
    },
    hero: {
      kicker: 'BEM-Nexus 指南',
      title: '产品帮助中心',
      description:
        '这里汇总当前 BEM-Nexus 工作空间能力: 仿真、聊天智能体、LLM 设置、知识库、工具系统、安全与导出工作流。',
      readyTitle: '当前可用',
      readyDescription:
        '仿真、聊天智能体、知识库、工具系统、安全登录、报告和可部署的工作空间持久化。',
      tags: {
        simulation: '仿真',
        agent: '智能体',
        knowledge: '知识',
        tools: '工具',
      },
    },
    sections: {
      workflow: '工作流指南',
      workflowDescription: '日常分析建议按此顺序使用。',
      moduleDirectory: '对应模块',
      moduleDirectoryDescription: '把每项产品能力映射到负责该能力的模块。',
      featureGuide: '功能指南',
      featureDescription: '高频界面的快速参考。',
      toolSystem: '工具系统边界',
      toolSystemDescription: '工具用于资源支撑操作、沙盒执行和可追踪 artifact。',
      currentGuides: '当前运行指南',
      currentGuidesDescription: '当前产品中已经稳定可用的行为。',
      operatingNotes: '运行提示',
      operatingDescription: '保障稳定使用的简短提醒。',
    },
    capabilities: {
      simulation: {
        title: '仿真',
        summary:
          '在同一工作空间准备 EnergyPlus 输入、确认输出、运行研究, 并检查图表、热力图、几何、日志和导出包。',
        points: {
          idfWorkflow: 'IDF 与 EPW 工作流',
          liveState: '实时运行状态与图表',
          exports: '2D、3D、日志和包导出',
        },
      },
      chat: {
        title: '聊天智能体',
        summary:
          '提出模型支持的问题, 查看智能体思考链, 调用已批准的 MCP 工具, 监控上下文预算, 并导出选中答案报告。',
        points: {
          markdown: 'Markdown 与公式渲染',
          trace: 'Trace 与上下文可见性',
          report: '选中会话报告导出',
        },
      },
      llmSettings: {
        title: 'LLM 设置',
        summary:
          '在界面中配置供应商和模型, 验证连接, 控制可用于聊天的模型, 并避免在普通响应中暴露原始凭据。',
        points: {
          records: '供应商与模型记录',
          tests: '连接测试',
          credentials: '凭据掩码与引用',
        },
      },
      knowledgeBase: {
        title: '知识库',
        summary:
          '创建资料库、上传工程参考资料、使用 Qwen embedding 索引文档、测试检索, 并预览带引用的来源分块。',
        points: {
          upload: '文档上传与资料库',
          indexing: '基于 embedding 的索引与重新索引',
          citations: '面向 grounded answer 的引用预览',
        },
      },
      toolSystem: {
        title: '工具系统',
        summary:
          '查看 EnergyPlus 操作、MCP 适配、Python sandbox 执行、工作空间文件、render contract 和 trace 输出的受治理边界。',
        points: {
          registry: '统一工具注册表与 profile',
          sandbox: 'Python sandbox 与工作空间限制',
          trace: '工具 trace、render 与 artifact contract',
        },
      },
      secureWorkspace: {
        title: '安全工作空间',
        summary:
          '使用单管理员设置流程、HttpOnly 浏览器会话、受保护 API 路由, 以及面向部署运行的工作空间持久化。',
        points: {
          setupToken: '初始设置令牌',
          recentAuth: '近期认证检查',
          databaseSettings: '数据库持久化设置',
        },
      },
    },
    moduleDirectory: {
      labels: {
        capability: '需要的能力',
        module: '使用模块',
        useWhen: '使用场景',
      },
      home: {
        title: '首页',
        capability: '查看六个主要工作界面和入口状态。',
        module: '首页',
        useWhen: '开始会话, 或判断任务应该进入哪个模块。',
      },
      visualization: {
        title: '可视化',
        capability: '准备并运行 EnergyPlus 仿真, 查看图表、热力图和几何。',
        module: '可视化',
        useWhen: '已有 IDF/EPW 资源, 需要直接操作仿真。',
      },
      chatAgent: {
        title: '聊天智能体',
        capability: '提出模型支持的问题、运行受治理工具, 并导出选中答案。',
        module: '聊天智能体',
        useWhen: '需要自然语言分析或工具支撑的自动化。',
      },
      llmSettings: {
        title: 'LLM 设置',
        capability: '配置聊天、推理、嵌入和外部检索供应商。',
        module: 'LLM 设置',
        useWhen: '需要新增或测试模型、embedding 或网页证据供应商。',
      },
      knowledgeBase: {
        title: '知识库',
        capability: '上传工程参考资料、构建 embedding, 并测试引用检索。',
        module: '知识库',
        useWhen: '答案需要项目手册、标准或上传参考资料支撑。',
      },
      toolSystem: {
        title: '工具系统',
        capability: '理解 MCP 工具、Python sandbox、工作空间工具、trace 和安全门禁。',
        module: '工具系统',
        useWhen: '任务依赖工具能力、工具边界或 artifact 行为。',
      },
      helpCenter: {
        title: '帮助中心',
        capability: '查看当前产品地图和运行指导。',
        module: '帮助中心',
        useWhen: '需要快速了解模块选择或稳定操作边界。',
      },
      secureWorkspace: {
        title: '安全工作空间',
        capability: '使用登录、近期认证、受保护 API 和持久化设置。',
        module: '设置、登录、LLM 设置',
        useWhen: '初始化部署或修改受保护配置。',
      },
      exports: {
        title: '导出与报告',
        capability: '保留仿真包、报告文件、图表、日志和 artifact。',
        module: '可视化、聊天智能体',
        useWhen: '需要保存与已检查运行或对话一致的结果。',
      },
      workspaceData: {
        title: '工作空间数据',
        capability: '管理上传资源、生成 artifact、日志和部署状态。',
        module: '可视化、聊天智能体、知识库',
        useWhen: '任务依赖已经上传或生成在工作空间中的文件。',
      },
    },
    workflow: {
      modelSetup: {
        title: '设置模型',
        text: '当聊天智能体、embedding 或外部证据尚未配置时, 先打开 LLM 设置。',
      },
      prepare: {
        title: '准备',
        text: '加载项目资源, 选择当前 IDF 和 EPW, 并在运行分析前确认所需输出。',
      },
      analyze: {
        title: '分析',
        text: '并行使用仿真视图和聊天智能体。当答案依赖运行时数据时, 保持 trace、上下文和工具状态可见。',
      },
      toolReview: {
        title: '检查工具',
        text: '当答案需要 EnergyPlus 工具、工作空间文件或 Python sandbox 执行时, 检查工具系统和 MCP 状态。',
      },
      export: {
        title: '导出',
        text: '从结果所属模块导出: 仿真模块导出运行包, 聊天智能体导出选中答案报告。',
      },
      preserve: {
        title: '持久化',
        text: '把生成文件、报告、日志、数据库记录和上传资源都视为工作空间部署资产。',
      },
    },
    features: {
      energyPlusTools: {
        title: 'EnergyPlus 工具',
        text: 'MCP 工具提供模型编辑、输出发现、计划表修改和运行检查, 并明确展示可用或阻塞状态。',
      },
      knowledgeBase: {
        title: '知识库',
        text: '用资料库管理手册、标准和仿真记录, 并为聊天智能体答案提供引用支撑。',
      },
      toolSystem: {
        title: '工具系统',
        text: '使用工具系统页面理解 MCP 适配、Agent-only Python、工作空间文件工具、trace、artifact 和安全门禁。',
      },
      reports: {
        title: '报告',
        text: '聊天报告保留选中的对话答案、trace 摘要、模型上下文和已附加的建筑文件。',
      },
      workspaceData: {
        title: '工作空间数据',
        text: '配置、资源、生成报告、上传、导出、日志和本地数据库文件都是部署资产。',
      },
      accessControl: {
        title: '访问控制',
        text: '当前面向单用户管理, 包含受保护的设置、登录、会话刷新和近期认证校验。',
      },
    },
    current: {
      modelSetup: {
        title: '模型设置',
        text: 'LLM 设置负责供应商记录、模型可用性、embedding 密钥、外部检索配置和连接测试。',
      },
      dailyOperation: {
        title: '日常操作',
        text: '用首页和侧边栏作为模块地图: 准备资源、运行仿真、向聊天智能体提问, 并从结果所属模块导出。',
      },
      resourceHandling: {
        title: '资源处理',
        text: '上传文件、生成 artifact、报告、日志和数据库记录都是工作空间资产, 属于部署状态的一部分。',
      },
      toolBoundaries: {
        title: '工具边界',
        text: 'EnergyPlus 操作需要匹配资源, 模型修改使用确认数据, 沙盒执行保持在受控工作空间中。',
      },
      exports: {
        title: '导出',
        text: '仿真包和聊天报告都从当前运行或会话生成, 确保保存结果与用户检查过的内容一致。',
      },
      helpCenter: {
        title: '帮助中心',
        text: '使用本页作为现有模块、能力归属和稳定运行边界的维护版产品地图。',
      },
    },
    toolSystemNotes: [
      '工具路由由当前轮证据、选中资源和工具 profile 元数据共同决定。',
      'Python 执行是 Agent-only fallback, 带有导入检查、运行时限制和工作空间 artifact 收集。',
      'Product-display、Agent-only、internal support 和 debug 工具拥有不同的可见性边界。',
    ],
    operatingNotes: [
      '使用聊天智能体前, 请至少配置一个可用聊天模型。',
      '将工作空间数据库和资源目录视为持久化部署数据。',
      '依赖工具型答案前, 请先检查 MCP 工具状态标记。',
      '从需要保留的当前会话或运行中导出报告。',
    ],
  },
  toolSystem: {
    hero: {
      kicker: 'Agent 工具平台',
      title: '工具系统',
      description:
        '工具系统是聊天智能体动作背后的受治理执行层。它把 MCP 适配、EnergyPlus 领域工具、Python sandbox 执行、工作空间文件操作、render contract、artifact、trace 和确认规则放在同一个显式边界内。',
      boundaryTitle: '有边界的执行',
      boundaryDescription:
        '只有当前任务证据、选中资源、schema 要求和安全策略同时匹配时, 工具才会运行。',
      tags: {
        mcp: 'MCP',
        energyPlus: 'EnergyPlus',
        python: 'Python',
        workspace: 'Workspace',
      },
    },
    sections: {
      platform: '平台层次',
      platformDescription: 'Agent 如何从用户任务路由到受治理的工具执行。',
      catalog: 'MCP 工具目录',
      catalogDescription: '按能力分类展示已注册工具, 并在每个工具旁标明执行边界。',
      sandbox: '沙盒与工作空间',
      sandboxDescription: '通用 Agent 工具与 EnergyPlus 领域工具保持边界分离。',
      boundaries: '安全边界',
      boundariesDescription: '每个工具都声明可见性、副作用和运行时边界。',
      workflow: '工具运行生命周期',
      workflowDescription: '可见 trace 覆盖 route、execute、observe 和 review 步骤。',
    },
    catalog: {
      labels: {
        capability: '能力',
        boundary: '边界',
      },
      groups: {
        catalog: {
          title: '目录与资源',
          description: '领域工具运行前使用的注册表和会话资源辅助工具。',
        },
        idfInspection: {
          title: 'IDF 检查',
          description: '读取上传模型结构、对象数量、计划表和内部负荷对象。',
        },
        idfModification: {
          title: 'IDF 修改与输出',
          description: '对模型变体和输出请求进行草拟、校验和确认式应用。',
        },
        simulation: {
          title: '仿真运行时',
          description: '检查 EnergyPlus 运行环境、准备命令、执行仿真并收集输出。',
        },
        resultsWeather: {
          title: '结果与天气',
          description: '读取 SQL 输出、生成摘要、校验 EPW 文件并创建可渲染概览。',
        },
        hvacTopology: {
          title: 'HVAC 拓扑',
          description: '提取 HVAC 回路结构和组件参数, 用于图形展示与检查。',
        },
        workspace: {
          title: '工作空间文件工具',
          description: 'Agent-only 的会话工作空间文件操作, 不暴露任意主机路径。',
        },
        pythonSandbox: {
          title: 'Python Sandbox',
          description: '基于 sandbox 的 Python 能力, 用于显式 fallback 分析、绘图和 artifact 创建。',
        },
      },
      tools: {
        eplus_mcp_tool_catalog: {
          capability: '列出已注册工具 contract、可见性、副作用和确认策略。',
          boundary: '只读的产品展示目录。',
        },
        eplus_model_resolve_path: {
          capability: '在当前会话工作空间内解析模型和天气资源引用。',
          boundary: '内部辅助; 仅限会话作用域查找。',
        },
        eplus_model_copy_file: {
          capability: '把模型或天气资源复制到受管理的工作空间位置。',
          boundary: '内部辅助; 只写入工作空间。',
        },
        eplus_idf_summary: {
          capability: '汇总上传 IDF 的对象数量和核心模型内容。',
          boundary: '只读; 需要 IDF 资源。',
        },
        eplus_idf_list_objects: {
          capability: '列出 IDF 对象类型和数量。',
          boundary: '只读; 需要 IDF 资源。',
        },
        eplus_idf_get_objects: {
          capability: '返回指定 IDF 对象类型的对象和字段。',
          boundary: '只读; 需要 IDF 资源和对象类型。',
        },
        eplus_schedule_inspect: {
          capability: '检查上传模型中的 Schedule 对象。',
          boundary: '只读; 需要 IDF 资源。',
        },
        eplus_people_inspect: {
          capability: '检查 People 内部负荷对象。',
          boundary: '只读; 需要 IDF 资源。',
        },
        eplus_lights_inspect: {
          capability: '检查 Lights 内部负荷对象。',
          boundary: '只读; 需要 IDF 资源。',
        },
        eplus_equipment_inspect: {
          capability: '检查 ElectricEquipment 内部负荷对象。',
          boundary: '只读; 需要 IDF 资源。',
        },
        eplus_schedule_patch_draft: {
          capability: '草拟 Schedule:Compact 数值 patch。',
          boundary: '模型修改草稿; 需要确认。',
        },
        eplus_people_density_adjust_draft: {
          capability: '为新 IDF 变体草拟 People 密度调整。',
          boundary: '模型修改草稿; 需要显式数值和确认。',
        },
        eplus_internal_load_patch_draft: {
          capability: '草拟 People、Lights 或 Equipment 对象字段修改。',
          boundary: '模型修改草稿; 需要确认。',
        },
        eplus_output_request_patch_draft: {
          capability: '草拟输出请求对象修改。',
          boundary: '模型修改草稿; 需要确认。',
        },
        eplus_idf_apply_patch: {
          capability: '把已确认 patch 应用到 IDF 变体。',
          boundary: '写入工作空间; 需要确认后的 patch 载荷。',
        },
        eplus_idf_save_variant: {
          capability: '把上传 IDF 保存为受管理的变体文件。',
          boundary: '写入工作空间; 需要确认。',
        },
        eplus_loads_modify_people: {
          capability: '创建 People 负荷修改。',
          boundary: '模型修改; 需要确认和 IDF 上下文。',
        },
        eplus_loads_validate_people: {
          capability: '在修改前后校验 People 负荷变化。',
          boundary: '基于 IDF 上下文的只读校验。',
        },
        eplus_loads_modify_lights: {
          capability: '创建照明负荷修改。',
          boundary: '模型修改; 需要确认和 IDF 上下文。',
        },
        eplus_loads_validate_lights: {
          capability: '校验照明负荷变化。',
          boundary: '基于 IDF 上下文的只读校验。',
        },
        eplus_loads_modify_equipment: {
          capability: '创建设备负荷修改。',
          boundary: '模型修改; 需要确认和 IDF 上下文。',
        },
        eplus_loads_validate_equipment: {
          capability: '校验设备负荷变化。',
          boundary: '基于 IDF 上下文的只读校验。',
        },
        eplus_output_get_variables: {
          capability: '列出已配置或可用的输出变量。',
          boundary: '只读; 需要 IDF 上下文。',
        },
        eplus_output_add_variables: {
          capability: '向模型添加输出变量请求。',
          boundary: '模型修改; 需要确认。',
        },
        eplus_output_get_meters: {
          capability: '列出已配置或可用的输出 meter。',
          boundary: '只读; 需要 IDF 上下文。',
        },
        eplus_output_add_meters: {
          capability: '向模型添加输出 meter 请求。',
          boundary: '模型修改; 需要确认。',
        },
        eplus_schedule_parse_text: {
          capability: '把自然语言计划表修改解析为结构化变化。',
          boundary: '内部辅助; 不直接写模型。',
        },
        eplus_schedule_apply_text: {
          capability: '把解析后的计划表修改应用到 IDF 变体。',
          boundary: '模型修改; 需要确认。',
        },
        eplus_runtime_check: {
          capability: '检查 EnergyPlus 可执行文件和 IDD 就绪状态。',
          boundary: '只读运行时检查。',
        },
        eplus_simulation_prepare: {
          capability: '在不运行仿真的情况下校验输入和命令形态。',
          boundary: '工作空间内准备; 需要 IDF, 可选 EPW。',
        },
        eplus_simulation_run: {
          capability: '基于已准备的模型和天气输入运行 EnergyPlus。',
          boundary: '仿真运行时执行; 输出仅进入工作空间。',
        },
        eplus_simulation_read_err: {
          capability: '读取 EnergyPlus ERR 输出用于诊断。',
          boundary: '只读工作空间输出检查。',
        },
        eplus_simulation_collect_outputs: {
          capability: '收集生成的仿真输出和 artifact。',
          boundary: '工作空间读写打包边界。',
        },
        eplus_simulation_server_status: {
          capability: '报告工具服务、运行时和会话工作空间状态。',
          boundary: '只读服务状态。',
        },
        eplus_sql_list_outputs: {
          capability: '列出可用 SQL 输出变量和 meter。',
          boundary: '只读 SQL 检查。',
        },
        eplus_sql_extract_timeseries: {
          capability: '提取所选输出的 SQL 时间序列。',
          boundary: '只读 SQL 提取; 需要输出选择。',
        },
        eplus_sql_monthly_summary: {
          capability: '从 SQL 结果生成月度摘要。',
          boundary: '只读分析; 返回结构化摘要。',
        },
        eplus_results_energy_temperature_overview: {
          capability: '从结果中构建能耗和温度概览数据。',
          boundary: '只读结果分析。',
        },
        eplus_results_render_overview: {
          capability: '为结果概览创建可渲染图表载荷。',
          boundary: '只读结果 render contract。',
        },
        eplus_epw_validate: {
          capability: '校验 EPW 天气文件结构和可用状态。',
          boundary: '只读; 需要 EPW 上下文。',
        },
        eplus_epw_summary: {
          capability: '汇总 EPW 地点、周期和天气字段。',
          boundary: '只读; 需要 EPW 上下文。',
        },
        eplus_epw_extract_timeseries: {
          capability: '提取 EPW 天气时间序列。',
          boundary: '只读提取; 需要字段选择。',
        },
        eplus_epw_monthly_stats: {
          capability: '计算 EPW 月度天气统计。',
          boundary: '只读天气分析。',
        },
        eplus_epw_render_weather_overview: {
          capability: '创建可渲染天气概览图表。',
          boundary: '只读天气 render contract。',
        },
        eplus_hvac_get_topology: {
          capability: '提取 plant、condenser 和 air-loop 拓扑。',
          boundary: '只读; 返回 topology graph 载荷。',
        },
        eplus_hvac_get_component_parameters: {
          capability: '检查 HVAC 组件字段值。',
          boundary: '只读; 需要 IDF 上下文。',
        },
        workspace_list_dir: {
          capability: '列出工作空间根目录下的文件和文件夹。',
          boundary: 'Agent-only; 工作空间只读。',
        },
        workspace_read_file: {
          capability: '读取工作空间内 UTF-8 文件。',
          boundary: 'Agent-only; 工作空间只读。',
        },
        workspace_search_text: {
          capability: '在工作空间文本文件中搜索字面匹配。',
          boundary: 'Agent-only; 工作空间只读。',
        },
        workspace_file_metadata: {
          capability: '不读取内容, 仅返回文件大小和元数据。',
          boundary: 'Agent-only; 工作空间只读。',
        },
        workspace_write_resource: {
          capability: '向工作空间写入文本资源。',
          boundary: 'Agent-only; 工作空间写入需要确认。',
        },
        workspace_copy_resource: {
          capability: '复制工作空间文件到受管理路径。',
          boundary: 'Agent-only; 工作空间写入需要确认。',
        },
        workspace_append_report_fragment: {
          capability: '向工作空间报告追加文本片段。',
          boundary: 'Agent-only; 工作空间写入需要确认。',
        },
        execute_python_capability_check: {
          capability: '检查 Python 导入、绘图、eppy 可用性和 artifact 限制。',
          boundary: 'Agent-only 诊断; 不提供普通用户执行按钮。',
        },
        execute_python_code: {
          capability: '运行显式 fallback Python, 用于分析、修复、转换、绘图和 artifact。',
          boundary: 'Agent-only 隔离沙盒, 受超时、allowlist 和工作空间限制。',
        },
      },
    },
    platform: {
      kernel: {
        title: '工具平台内核',
        text: '统一注册表定义每个工具的 profile、输入 schema、路由策略、render contract 和公开结果形态。',
        points: {
          profiles: 'Profile 元数据驱动路由和展示',
          results: '工具结果使用统一结构化 envelope',
          adapters: 'Web catalog、FastMCP 和模型工具 schema 共享元数据',
        },
      },
      mcp: {
        title: 'MCP 适配层',
        text: 'MCP 保持为兼容工具元数据暴露的适配层, 产品运行时使用后端工具注册表。',
        points: {
          catalog: '目录卡片展示 ready 或 blocked 状态',
          fastmcp: '保持 FastMCP 兼容的工具暴露方式',
          metadata: '显式展示 audience、family、capability 和 render 类型',
        },
      },
      energyPlus: {
        title: 'EnergyPlus 领域工具',
        text: '上传的 IDF、EPW、SQL 和仿真输出会激活检查、patch、运行时检查、结果解析和图表工具。',
        points: {
          idf: 'IDF 检查与确认式 patch 工作流',
          epw: 'EPW 校验与天气概览 artifact',
          results: 'SQL 输出、摘要和可渲染图表载荷',
        },
      },
    },
    sandbox: {
      python: {
        title: 'Python Sandbox',
        text: 'Python 作为 Agent-only fallback, 用于显式的可编程分析、修复、转换和 artifact 创建, 并限制在会话工作空间中。',
      },
      workspace: {
        title: '工作空间文件工具',
        text: '工作空间工具通过策略校验的相对引用读取、搜索、复制、写入和总结资源文件, 而不是暴露主机路径。',
      },
      artifacts: {
        title: 'Artifact 与 Render',
        text: '生成的图像、表格、拓扑图、图表数据、文本载荷和文件会以结构化 render 指令和公开 artifact 返回。',
      },
    },
    flow: {
      route: {
        title: '路由',
        text: 'Planner 和 Router 根据当前轮 intent、可用资源、schema、前置条件和 profile 元数据给工具评分。',
      },
      execute: {
        title: '执行',
        text: 'Executor 校验参数, 注入安全资源上下文, 运行 handler, 并记录 schema、call、result 和 artifact 事件。',
      },
      review: {
        title: '审查',
        text: 'Reviewer 检查 validation 状态、缺失上下文、确认需求, 以及工具结果是否足够支撑最终答案。',
      },
    },
    safeguards: [
      'Product-display、Agent-only、internal support 和 debug 工具在 UI 渲染前已经分离。',
      '模型修改操作必须来自显式数值或确认载荷; 隐藏默认值不会被当作已知用户意图。',
      'Python 导入受 allowlist 控制, 执行受会话工作空间、超时、输出和 artifact 规则约束。',
      '工具输出必须暴露结构化数据、render 指令、validation、trace、artifact 和建议下一步。',
    ],
  },
  chat: {
    title: '聊天智能体',
    session: {
      newTitle: '新会话',
      recoveredTask: '已恢复任务',
      autoGeneratedTask: '自动生成任务',
    },
    sidebar: {
      sessions: '会话',
      mcpTools: 'MCP 工具',
      toolCount: '21 个工具',
      contextBudget: '预算',
    },
    actions: {
      newSession: '新建',
      deleteSession: '删除',
      renameSession: '重命名会话',
      saveSessionTitle: '保存会话名称',
      cancelSessionTitle: '取消重命名',
      exportReport: '报告',
      refreshModels: '刷新可用模型',
      stop: '停止',
      send: '发送',
    },
    model: {
      label: '模型',
      noUsableModels: '没有可用的 LLM 模型。请打开 LLM 设置并完成一次成功的连接测试。',
      noUsableModelsOption: '无可用模型',
      loadFailure: '加载可用 LLM 模型失败。',
      streaming: '生成中...',
    },
    sources: {
      knowledgeBase: '项目资料',
      knowledgeBaseReady: '相关时使用已索引的项目资料。',
      noKnowledgeBase: '无可用项目资料',
      webSearch: '联网',
    },
    empty: {
      title: '开始对话',
      description:
        '可以直接提问, 也可以上传 IDF/EPW 后发送模型任务, 例如“检查人员对象, 然后添加输出变量”。',
    },
    composer: {
      placeholder: '发送消息...',
    },
    attachments: {
      noIdf: '未选择 IDF',
      noEpw: '未选择 EPW',
    },
    failures: {
      exportReport: '导出报告失败。',
      renameSession: '重命名会话失败。',
      renameUnavailable: '请先发送一条消息, 再重命名该会话。',
      stream: '流式响应失败。',
      request: '请求失败。',
    },
    events: {
      agentDidNotFinish: '智能体未成功完成。',
      agentStopped: '智能体在 {phase} 阶段停止: {detail}',
      modelContextLoaded: '模型上下文已加载。',
      contextUpdated: '上下文已更新。',
      loadedMemoryHints: '已加载记忆提示: {hints}',
    },
    contextGauge: {
      title: '上下文仪表',
      tokens: '{count} 令牌',
      estimatedTokens: '估算 {count} 令牌',
      budgetSource: {
        backend: '后端预算',
        fallback: '降级估算',
      },
      degraded: {
        title: '上下文降级',
        fallbackReason: '滑动窗口降级策略已启用。',
      },
      states: {
        hardGuard: '硬限制',
        compressing: '压缩中',
        compressed: '已压缩',
        warning: '警告',
        notice: '提示',
        safe: '安全',
      },
      sources: {
        providerUsage: '供应商用量',
        tokenizer: 'Tokenizer',
        characterEstimate: '字符估算',
      },
      breakdown: {
        messages: '消息',
        system: '系统',
        thoughtChain: '思考链',
        toolPayload: '工具载荷',
        memory: '记忆',
        compression: '压缩',
        resources: '资源',
        providerPrompt: '供应商提示',
      },
      metrics: {
        modelMax: '模型上限',
        availableInput: '可用输入',
        responseReserve: '响应预留',
        estimateSource: '估算来源',
        compressionState: '压缩状态',
        thresholds: '阈值',
      },
    },
  },
}

export default messages
