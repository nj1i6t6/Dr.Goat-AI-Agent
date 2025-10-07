在你的前端代码 frontend/src/stores/iot.js 中，定义了一个 DEVICE_TYPE_CATALOG，这便是你目前在系统中预设的所有设备类型及其分类：
感测器 (Sensor):
舍内环境监控 (主要模拟温度、湿度、气体浓度等)
智慧颈圈/耳标 (主要模拟羊只体温、活动量等生理数据)
电子药丸/瘤胃监测器
自动体重计
自动化挤乳系统
智慧採食槽 (模拟采食量、时长)
智慧饮水器 (模拟饮水量、频率)
饲料/草料库存感测器
GPS 定位项圈
AI 视觉摄影机
致动器 (Actuator):
自动分群门
自动风扇
雾化降温系统
遮阳网/窗簾控制器
电磁阀
自动喷雾/消毒系统
手动添加并运行新测试 IoT 设备的完整流程
我们将以添加一个**“智慧颈圈/耳标”**类型的模拟器为例。
步骤 1：在前端创建新的 IoT 设备
启动现有应用： 确保你的 Docker 环境正在运行 (docker compose up -d)。
访问前端页面： 打开浏览器，进入 http://localhost:3000。
登录并进入 IoT 管理： 登录你的账号，然后点击导航栏的「智慧牧场 IoT」。
新增装置：
点击「新增装置」按钮。
名称： 填入一个有意义的名字，例如 模拟智慧颈圈-A001。
装置类型： 从下拉列表中选择 智慧颈圈/耳標。
分类： 确保选择的是 感测器。
位置 (可选): 可以填入 A 区羊舍。
点击「建立装置」。
复制 API Key：
创建成功后，会弹出一个对话框，里面有一串一次性显示的 API Key。
立即复制这串新的 API Key！ 比如：a1b2c3d4e5f6g7h8i9j0...
你现在有了一个新的设备记录在数据库里，并且拿到它的专属通行证 (API Key)。
步骤 2：修改 docker-compose.yml 添加新的模拟器服务
现在，我们要告诉 Docker Compose 启动第二个模拟器容器，专门模拟这个新的颈圈设备。
打开 docker-compose.yml 文件。
复制并修改： 复制现有的 iot_simulator 服务定义，然后把它贴在下面，并改名为 iot_simulator_wearable (或者任何你喜欢的名字)。
code
Yaml
# docker-compose.yml

services:
  # ... db, redis, backend, frontend, iot_simulator 的定义保持不变 ...

  # ↓↓↓ 复制现有的 iot_simulator，然后修改成下面这样 ↓↓↓
  iot_simulator_wearable: # <--- 1. 服务名称改成新的，不能重复
    build:
      context: ./iot_simulator
      dockerfile: Dockerfile
    container_name: goat-nutrition-simulator-wearable # <-- 2. 容器名也改一下
    depends_on:
      - backend
    environment:
      # 3. 把第一步复制的新 API Key 贴在这里！
      API_KEY: "a1b2c3d4e5f6g7h8i9j0..." 

      # 4. URL 保持不变
      INGEST_URL: "http://backend:5001/api/iot/ingest"

      # 5. 修改设备类型为你想要模拟的类型
      DEVICE_TYPE: "wearable_tag"  # <-- 对应模拟器代码中的类型
      
      # 6. 发送间隔可以调一下，以便区分
      SEND_INTERVAL_SECONDS: 25 
    restart: unless-stopped
    networks:
      - goat-network

# ... volumes 和 networks 的定义保持不变 ...
重要： DEVICE_TYPE 的值需要和你 iot_simulator.py 脚本中的 mapping 字典的键匹配。根据之前的代码，"智慧颈圈/耳標" 对应的模拟器类型是 "wearable_tag"。
步骤 3：重新启动 Docker Compose
现在你的编排文件已经更新，需要让 Docker Compose 应用这些变更。
保存你修改后的 docker-compose.yml 文件。
回到终端，执行以下指令：
code
Bash
# 使用 up 指令，它会自动检测到新增的服务并只创建和启动它
# --build 是好习惯，确保镜像也是最新的
docker compose up --build -d
Docker Compose 会发现多了一个 iot_simulator_wearable 服务，然后会为它构建镜像并启动容器。
步骤 4：验证新模拟器是否正常工作
查看新模拟器的日志：
code
Bash
docker compose logs -f iot_simulator_wearable
你应该会看到它每 25 秒发送一次数据，并且数据内容是关于体温 (body_temperature)、活动指数 (activity_index) 等，这证明它正在模拟颈圈设备。
code
Code
[INFO] - 已送出模擬數據: {"data": {"ear_num": "E123", "body_temperature": 38.9, ...}}
查看后端日志：
code
Bash
docker compose logs -f backend
你会看到 POST /api/iot/ingest 201 的日志交替出现，来源是两个不同的模拟器。
回到前端页面：
刷新「智慧牧场 IoT」页面。
你应该会在设备列表中看到你新创建的 模拟智慧颈圈-A001 这个设备。
它的状态应该很快会变成**“在线”**。
点击这个新设备，在右侧的详情抽屉里，“最近读数”图表应该会开始显示出来自这个新模拟器的体温、活动指数等数据曲线。
流程总结：
前端/API 创建设备 -> 获得 Key
docker-compose.yml 新增服务 -> 填入 Key 和设备类型
docker compose up 启动新服务
日志和前端验证
通过这套流程，你可以根据需要启动任意多个、任意类型的模拟器，来完整地测试你的 IoT 系统。