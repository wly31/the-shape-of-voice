# SignTranslate 系统设计文档


## 一、数据库设计

## E-R图

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│    User     │       │   Recognition   │       │    Sign     │
│    用户     │──1:N──│    Record       │──N:M──│    Word     │
│             │       │   识别记录      │       │   手语词汇   │
└─────────────┘       └─────────────────┘       └─────────────┘

字段说明：
- User: id, username, password
- RecognitionRecord: id, user_id, result, confidence, created_at
- SignWord: id, word, video_url
```

---

## 二、接口设计


---

## 三、前端设计


---
**创建日期**：2026-05-28
