# SignTranslate 数据库E-R图设计

## 一、E-R图（实体-关系图）

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    SignTranslate E-R图                                   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌──────────────┐                                              ┌──────────────┐       │
│   │              │                                              │              │       │
│   │     用户     │                                              │   手语词汇   │       │
│   │    User      │                                              │  SignWord    │       │
│   │              │                                              │              │       │
│   ├──────────────┤                                              ├──────────────┤       │
│   │ PK id        │                                              │ PK id        │       │
│   │    username  │                                              │    word      │       │
│   │    password  │                                              │    pinyin    │       │
│   │    email     │                                              │    category  │       │
│   │    is_staff  │                                              │    video_url │       │
│   │    created_at│                                              │    created_at│       │
│   │              │                                              │              │       │
│   └──────┬───────┘                                              └──────┬───────┘       │
│          │                                                           │                │
│          │ 1                                                         │ 1              │
│          │                                                           │                │
│          │ N                                                         │ N              │
│          ▼                                                           ▼                │
│   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐                  │
│   │              │         │              │         │              │                  │
│   │   识别记录   │◄────────┤   动画记录   ├────────►│   词汇映射   │                  │
│   │ Recognition  │    1:1  │  Animation   │   N:M   │ WordMapping  │                  │
│   │   Record     │         │   Record     │         │              │                  │
│   │              │         │              │         │              │                  │
│   ├──────────────┤         ├──────────────┤         ├──────────────┤                  │
│   │ PK id        │         │ PK id        │         │ PK id        │                  │
│   │ FK user_id   │         │ FK rec_id    │         │ FK anim_id   │                  │
│   │    result    │         │    text_input│         │ FK word_id   │                  │
│   │    confidence│         │    video_url │         │    sequence  │                  │
│   │    image_url │         │    duration  │         │              │                  │
│   │    mode      │         │    created_at│         │              │                  │
│   │    created_at│         │              │         │              │                  │
│   │              │         │              │         │              │                  │
│   └──────────────┘         └──────────────┘         └──────────────┘                  │
│                                                                                          │
│   ┌──────────────┐         ┌──────────────┐                                            │
│   │              │         │              │                                            │
│   │   系统配置   │         │   操作日志   │                                            │
│   │   Config     │         │    Log       │                                            │
│   │              │         │              │                                            │
│   ├──────────────┤         ├──────────────┤                                            │
│   │ PK id        │         │ PK id        │                                            │
│   │    key       │         │ FK user_id   │                                            │
│   │    value     │         │    action    │                                            │
│   │    updated_at│         │    details   │                                            │
│   │              │         │    ip_addr   │                                            │
│   │              │         │    created_at│                                            │
│   │              │         │              │                                            │
│   └──────────────┘         └──────────────┘                                            │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘

图例说明:
┌───┐ = 实体(Entity)    PK = 主键(Primary Key)    FK = 外键(Foreign Key)
─── = 关系(Relationship)    1:N = 一对多    N:M = 多对多    1:1 = 一对一
```

---

## 二、实体详细说明

### 2.1 用户实体 (User)

```
┌─────────────────────────────────────────────────────────────────┐
│                          User (用户)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   属性名     │    数据类型   │    约束      │    说明      │ │
│  ├──────────────┼──────────────┼──────────────┼──────────────┤ │
│  │ id           │ INTEGER      │ PK, AUTO     │ 用户ID       │ │
│  │ username     │ VARCHAR(50)  │ UNIQUE, NOT  │ 用户名       │ │
│  │              │              │ NULL         │              │ │
│  │ password     │ VARCHAR(128) │ NOT NULL     │ 密码(加密)   │ │
│  │ email        │ VARCHAR(100) │ UNIQUE       │ 邮箱         │ │
│  │ is_staff     │ BOOLEAN      │ DEFAULT 0    │ 是否管理员   │ │
│  │ is_active    │ BOOLEAN      │ DEFAULT 1    │ 是否激活     │ │
│  │ last_login   │ DATETIME     │ NULL         │ 最后登录时间 │ │
│  │ created_at   │ DATETIME     │ DEFAULT NOW  │ 创建时间     │ │
│  │ updated_at   │ DATETIME     │ DEFAULT NOW  │ 更新时间     │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                 │
│  关系: 1:N → RecognitionRecord (一个用户有多条识别记录)         │
│        1:N → Log (一个用户有多条操作日志)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 识别记录实体 (RecognitionRecord)

```
┌─────────────────────────────────────────────────────────────────┐
│                    RecognitionRecord (识别记录)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   属性名     │    数据类型   │    约束      │    说明      │ │
│  ├──────────────┼──────────────┼──────────────┼──────────────┤ │
│  │ id           │ INTEGER      │ PK, AUTO     │ 记录ID       │ │
│  │ user_id      │ INTEGER      │ FK → User    │ 用户ID       │ │
│  │ result       │ VARCHAR(50)  │ NOT NULL     │ 识别结果     │ │
│  │ confidence   │ FLOAT        │ 0-1范围      │ 置信度       │ │
│  │ image_url    │ VARCHAR(255) │ NULL         │ 图像路径     │ │
│  │ mode         │ VARCHAR(20)  │ DEFAULT      │ 识别模式     │ │
│  │              │              │ 'english'    │ english/     │ │
│  │              │              │              │ chinese      │ │
│  │ bbox_x       │ INTEGER      │ NULL         │ 边界框X坐标  │ │
│  │ bbox_y       │ INTEGER      │ NULL         │ 边界框Y坐标  │ │
│  │ bbox_w       │ INTEGER      │ NULL         │ 边界框宽度   │ │
│  │ bbox_h       │ INTEGER      │ NULL         │ 边界框高度   │ │
│  │ created_at   │ DATETIME     │ DEFAULT NOW  │ 创建时间     │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                 │
│  关系: N:1 → User (多条记录属于一个用户)                        │
│        1:1 → AnimationRecord (可选，一条记录可生成一个动画)     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 动画记录实体 (AnimationRecord)

```
┌─────────────────────────────────────────────────────────────────┐
│                    AnimationRecord (动画记录)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   属性名     │    数据类型   │    约束      │    说明      │ │
│  ├──────────────┼──────────────┼──────────────┼──────────────┤ │
│  │ id           │ INTEGER      │ PK, AUTO     │ 动画ID       │ │
│  │ rec_id       │ INTEGER      │ FK →         │ 关联识别记录 │ │
│  │              │              │ Recognition  │ (可选)       │ │
│  │              │              │ NULL         │              │ │
│  │ text_input   │ VARCHAR(500) │ NOT NULL     │ 输入文本     │ │
│  │ video_url    │ VARCHAR(255) │ NOT NULL     │ 视频文件路径 │ │
│  │ duration     │ FLOAT        │ NULL         │ 视频时长(秒) │ │
│  │ file_size    │ INTEGER      │ NULL         │ 文件大小(B)  │ │
│  │ status       │ VARCHAR(20)  │ DEFAULT      │ 生成状态     │ │
│  │              │              │ 'completed'  │ pending/     │ │
│  │              │              │              │ processing/  │ │
│  │              │              │              │ completed/   │ │
│  │              │              │              │ failed       │ │
│  │ created_at   │ DATETIME     │ DEFAULT NOW  │ 创建时间     │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                 │
│  关系: 1:1 → RecognitionRecord (可选，由识别记录生成)           │
│        1:N → WordMapping (一个动画包含多个词汇)                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4 手语词汇实体 (SignWord)

```
┌─────────────────────────────────────────────────────────────────┐
│                      SignWord (手语词汇)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   属性名     │    数据类型   │    约束      │    说明      │ │
│  ├──────────────┼──────────────┼──────────────┼──────────────┤ │
│  │ id           │ INTEGER      │ PK, AUTO     │ 词汇ID       │ │
│  │ word         │ VARCHAR(50)  │ UNIQUE, NOT  │ 词汇(中文)   │ │
│  │              │              │ NULL         │              │ │
│  │ pinyin       │ VARCHAR(100) │ NULL         │ 拼音         │ │
│  │ category     │ VARCHAR(50)  │ NULL         │ 分类         │ │
│  │              │              │              │ 日常/数字/   │ │
│  │              │              │              │ 情感/动作等  │ │
│  │ video_url    │ VARCHAR(255) │ NULL         │ 示范视频路径 │ │
│  │ image_url    │ VARCHAR(255) │ NULL         │ 示范图片路径 │ │
│  │ difficulty   │ INTEGER      │ DEFAULT 1    │ 难度等级1-5  │ │
│  │ usage_count  │ INTEGER      │ DEFAULT 0    │ 使用次数     │ │
│  │ is_active    │ BOOLEAN      │ DEFAULT 1    │ 是否启用     │ │
│  │ created_at   │ DATETIME     │ DEFAULT NOW  │ 创建时间     │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                 │
│  关系: 1:N → WordMapping (一个词汇可出现在多个动画中)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.5 词汇映射实体 (WordMapping) - 关联表

```
┌─────────────────────────────────────────────────────────────────┐
│                   WordMapping (词汇映射)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   属性名     │    数据类型   │    约束      │    说明      │ │
│  ├──────────────┼──────────────┼──────────────┼──────────────┤ │
│  │ id           │ INTEGER      │ PK, AUTO     │ 映射ID       │ │
│  │ anim_id      │ INTEGER      │ FK →         │ 动画ID       │ │
│  │              │              │ Animation    │              │ │
│  │ word_id      │ INTEGER      │ FK → SignWord│ 词汇ID       │ │
│  │ sequence     │ INTEGER      │ NOT NULL     │ 顺序号       │ │
│  │ start_time   │ FLOAT        │ NULL         │ 开始时间(秒) │ │
│  │ end_time     │ FLOAT        │ NULL         │ 结束时间(秒) │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                 │
│  关系: N:1 → AnimationRecord (多条映射属于一个动画)             │
│        N:1 → SignWord (多条映射指向一个词汇)                    │
│                                                                 │
│  说明: 这是一个多对多关联表，记录动画中包含的词汇及顺序         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.6 系统配置实体 (Config)

```
┌─────────────────────────────────────────────────────────────────┐
│                       Config (系统配置)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   属性名     │    数据类型   │    约束      │    说明      │ │
│  ├──────────────┼──────────────┼──────────────┼──────────────┤ │
│  │ id           │ INTEGER      │ PK, AUTO     │ 配置ID       │ │
│  │ config_key   │ VARCHAR(100) │ UNIQUE, NOT  │ 配置键       │ │
│  │              │              │ NULL         │              │ │
│  │ config_value │ TEXT         │ NULL         │ 配置值       │ │
│  │ description  │ VARCHAR(255) │ NULL         │ 配置说明     │ │
│  │ updated_at   │ DATETIME     │ DEFAULT NOW  │ 更新时间     │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                 │
│  示例配置:                                                      │
│  - recognition_threshold: 0.8 (识别置信度阈值)                  │
│  - max_frame_rate: 10 (最大帧率)                                │
│  - enable_tts: true (是否启用语音播报)                          │
│  - default_language: 'zh-CN' (默认语言)                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.7 操作日志实体 (Log)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Log (操作日志)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   属性名     │    数据类型   │    约束      │    说明      │ │
│  ├──────────────┼──────────────┼──────────────┼──────────────┤ │
│  │ id           │ INTEGER      │ PK, AUTO     │ 日志ID       │ │
│  │ user_id      │ INTEGER      │ FK → User    │ 用户ID       │ │
│  │              │              │ NULL         │ (匿名用户)   │ │
│  │ action       │ VARCHAR(50)  │ NOT NULL     │ 操作类型     │ │
│  │              │              │              │ recognize/   │ │
│  │              │              │              │ animate/     │ │
│  │              │              │              │ login/       │ │
│  │              │              │              │ logout等     │ │
│  │ details      │ TEXT         │ NULL         │ 操作详情     │ │
│  │ ip_address   │ VARCHAR(45)  │ NULL         │ IP地址       │ │
│  │ user_agent   │ VARCHAR(255) │ NULL         │ 浏览器信息   │ │
│  │ created_at   │ DATETIME     │ DEFAULT NOW  │ 创建时间     │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                 │
│  关系: N:1 → User (多条日志属于一个用户)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、关系说明

```
┌─────────────────────────────────────────────────────────────────┐
│                         实体关系总览                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  关系名称          │  类型   │  说明                        ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │  User →            │  1:N    │  一个用户有多条识别记录       ││
│  │ RecognitionRecord  │         │                              ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │  User → Log        │  1:N    │  一个用户有多条操作日志       ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │  RecognitionRecord │  1:1    │  一条识别记录可生成一个       ││
│  │ → AnimationRecord  │ (可选)  │  动画记录(可选)              ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │  AnimationRecord → │  1:N    │  一个动画包含多条词汇映射     ││
│  │ WordMapping        │         │                              ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │  SignWord →        │  1:N    │  一个词汇可出现在多个         ││
│  │ WordMapping        │         │  动画中                      ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │  AnimationRecord   │  N:M    │  通过WordMapping关联，        ││
│  │ ↔ SignWord         │ (间接)  │  一个动画包含多个词汇，       ││
│  │                    │         │  一个词汇可出现在多个动画     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、数据库表结构（SQL）

```sql
-- 1. 用户表
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    email VARCHAR(100) UNIQUE,
    is_staff BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. 手语词汇表
CREATE TABLE sign_word (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word VARCHAR(50) UNIQUE NOT NULL,
    pinyin VARCHAR(100),
    category VARCHAR(50),
    video_url VARCHAR(255),
    image_url VARCHAR(255),
    difficulty INTEGER DEFAULT 1,
    usage_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. 识别记录表
CREATE TABLE recognition_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    result VARCHAR(50) NOT NULL,
    confidence FLOAT,
    image_url VARCHAR(255),
    mode VARCHAR(20) DEFAULT 'english',
    bbox_x INTEGER,
    bbox_y INTEGER,
    bbox_w INTEGER,
    bbox_h INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- 4. 动画记录表
CREATE TABLE animation_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rec_id INTEGER,
    text_input VARCHAR(500) NOT NULL,
    video_url VARCHAR(255) NOT NULL,
    duration FLOAT,
    file_size INTEGER,
    status VARCHAR(20) DEFAULT 'completed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rec_id) REFERENCES recognition_record(id)
);

-- 5. 词汇映射表（关联表）
CREATE TABLE word_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anim_id INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    sequence INTEGER NOT NULL,
    start_time FLOAT,
    end_time FLOAT,
    FOREIGN KEY (anim_id) REFERENCES animation_record(id),
    FOREIGN KEY (word_id) REFERENCES sign_word(id)
);

-- 6. 系统配置表
CREATE TABLE config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description VARCHAR(255),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. 操作日志表
CREATE TABLE log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(50) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

---

## 五、E-R图简化版（快速参考）

```
┌─────────────────────────────────────────────────────────────────┐
│                     E-R图简化版                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────┐       ┌─────────┐       ┌─────────┐              │
│   │  User   │───1:N─│  Record │───1:1─│  Anim   │              │
│   │  用户   │       │  识别记录│       │  动画   │              │
│   └─────────┘       └─────────┘       └────┬────┘              │
│                                            │                   │
│                                            │ 1:N               │
│                                            ▼                   │
│                                      ┌───────────┐             │
│                                      │WordMapping│             │
│                                      │  词汇映射  │             │
│                                      └─────┬─────┘             │
│                                            │                   │
│                                            │ N:1               │
│                                            ▼                   │
│                                      ┌───────────┐             │
│                                      │ SignWord  │             │
│                                      │  手语词汇  │             │
│                                      └───────────┘             │
│                                                                 │
│   ┌─────────┐       ┌─────────┐                                │
│   │  Config │       │   Log   │                                │
│   │  配置   │       │  日志   │                                │
│   └─────────┘       └─────────┘                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

**文档版本**：v1.0  
**创建日期**：2026-05-28
