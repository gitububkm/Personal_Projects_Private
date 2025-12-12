"""
Модуль для работы с Prometheus метриками
"""
import json
import os
from pathlib import Path
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any
from datetime import datetime

# Бизнес-метрики
NEWS_CREATED_TOTAL = Counter("news_created_total", "Total number of news created")
USERS_REGISTERED_TOTAL = Counter(
    "users_registered_total", "Total number of registered users"
)
NOTIFICATIONS_SENT_TOTAL = Counter(
    "notifications_sent_total", "Total number of notifications sent", ["type"]
)

# Для обратной совместимости
news_created_total = NEWS_CREATED_TOTAL
users_registered_total = USERS_REGISTERED_TOTAL
notifications_sent_total = NOTIFICATIONS_SENT_TOTAL


class MetricsExporter:
    """Класс для экспорта метрик в JSON файл"""
    
    def __init__(self, metrics_file: str = "metrics.json"):
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
    
    def export_metrics(self) -> Dict[str, Any]:
        """Экспортирует все метрики в словарь"""
        from prometheus_client import REGISTRY
        from prometheus_client.parser import text_string_to_metric_families
        
        metrics_data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {}
        }
        
        # Получаем метрики в текстовом формате и парсим их
        try:
            metrics_text = generate_latest(REGISTRY).decode('utf-8')
            for family in text_string_to_metric_families(metrics_text):
                samples = []
                for sample in family.samples:
                    samples.append({
                        "name": sample.name,
                        "labels": dict(sample.labels) if sample.labels else {},
                        "value": sample.value
                    })
                metrics_data["metrics"][family.name] = {
                    "type": family.type,
                    "help": family.documentation,
                    "samples": samples
                }
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.error("failed_to_export_metrics", error=str(e))
        
        return metrics_data
    
    def save_metrics_to_file(self):
        """Сохраняет метрики в JSON файл"""
        try:
            metrics_data = self.export_metrics()
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            import structlog
            logger = structlog.get_logger()
            logger.error("failed_to_save_metrics", error=str(e))


# Глобальный экземпляр экспортера
metrics_exporter = MetricsExporter(
    metrics_file=os.getenv("METRICS_FILE", "logs/metrics.json")
)

