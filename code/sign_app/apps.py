import os
import threading

from django.apps import AppConfig


class SignAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sign_app"

    def ready(self):
        # runserver 子进程启动后后台预热词库，避免首次上传等待过久
        if os.environ.get("RUN_MAIN") != "true":
            return

        def _warm():
            try:
                from .sign_lexicon import warm_vocab_sketch_cache
                warm_vocab_sketch_cache()
            except Exception as exc:
                print(f"词库预热跳过: {exc}")

        threading.Thread(target=_warm, daemon=True, name="vocab-warmup").start()
