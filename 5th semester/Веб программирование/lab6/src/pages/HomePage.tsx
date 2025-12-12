import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { newsApi } from "../api/news";
import { NewsCard } from "../components/NewsCard";
import { useAuth } from "../context/AuthContext";
import { canCreateNews } from "../lib/roleUtils";
import type { NewsItem } from "../types";

export const HomePage = () => {
  const { user } = useAuth();
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadNews = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await newsApi.list({ limit: 50 });
      setNews(data);
    } catch (err) {
      console.error(err);
      setError("Не удалось загрузить новости. Попробуйте позже.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadNews();
  }, []);

  return (
    <div className="stack-lg">
      <section className="card">
        <div className="section-head">
          <div>
            <h1>Новости</h1>
            <p className="muted">Просматривайте публикации и открывайте детали, чтобы обсудить.</p>
          </div>
          <div className="section-actions">
            <button type="button" className="btn btn-secondary" onClick={() => void loadNews()}>
              Обновить
            </button>
            {canCreateNews(user) && (
              <Link to="/create-news" className="btn btn-primary">
                Создать новость
              </Link>
            )}
          </div>
        </div>
      </section>

      {error && <p className="error">{error}</p>}
      {loading ? (
        <p>Загрузка ленты...</p>
      ) : (
        <div className="news-grid">
          {news.length === 0 && <p>Пока нет опубликованных новостей.</p>}
          {news.map((item) => (
            <NewsCard key={item.id} news={item} />
          ))}
        </div>
      )}
    </div>
  );
};


