import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import dayjs from "dayjs";

import { commentsApi } from "../api/comments";
import { newsApi } from "../api/news";
import { CommentList } from "../components/CommentList";
import { CommentForm } from "../components/forms/CommentForm";
import { useAuth } from "../context/AuthContext";
import { canManageComment, canManageNews } from "../lib/roleUtils";
import type { CommentItem, NewsItem } from "../types";

export const NewsPage = () => {
  const { id } = useParams();
  const newsId = Number(id);
  const navigate = useNavigate();
  const { user } = useAuth();

  const [news, setNews] = useState<NewsItem | null>(null);
  const [comments, setComments] = useState<CommentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [commentError, setCommentError] = useState<string | null>(null);

  const load = async () => {
    if (Number.isNaN(newsId)) {
      setError("Неверный идентификатор новости");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [newsData, commentsData] = await Promise.all([
        newsApi.get(newsId),
        commentsApi.listByNews(newsId)
      ]);
      setNews(newsData);
      setComments(commentsData);
    } catch (err) {
      console.error(err);
      setError("Не удалось загрузить новость");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [newsId]);


  const handleDeleteNews = async () => {
    if (!news) return;
    if (!window.confirm("Удалить новость и связанные комментарии?")) {
      return;
    }
    try {
      await newsApi.remove(news.id);
      navigate("/");
    } catch (err) {
      console.error(err);
      setError("Не удалось удалить новость");
    }
  };

  const handleCreateComment = async (text: string) => {
    if (!news) return;
    setCommentError(null);
    try {
      const created = await commentsApi.create({ news_id: news.id, text: text.trim() });
      setComments((prev) => [...prev, created]);
    } catch (err) {
      console.error(err);
      setCommentError("Не удалось добавить комментарий");
    }
  };

  const handleUpdateComment = async (commentId: number, text: string) => {
    try {
      const updated = await commentsApi.update(commentId, { text });
      setComments((prev) => prev.map((item) => (item.id === commentId ? updated : item)));
    } catch (err) {
      console.error(err);
      setCommentError("Не удалось обновить комментарий");
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    if (!window.confirm("Удалить комментарий?")) {
      return;
    }
    try {
      await commentsApi.remove(commentId);
      setComments((prev) => prev.filter((item) => item.id !== commentId));
    } catch (err) {
      console.error(err);
      setCommentError("Не удалось удалить комментарий");
    }
  };

  const canManageCurrentNews = news && user ? canManageNews(user, news) : false;

  if (loading) {
    return <p>Загрузка...</p>;
  }

  if (error) {
    return (
      <div className="stack-sm">
        <p className="error">{error}</p>
        <Link to="/" className="btn btn-secondary">
          Вернуться на главную
        </Link>
      </div>
    );
  }

  if (!news) {
    return (
      <div className="stack-sm">
        <p>Новость не найдена.</p>
        <Link to="/" className="btn btn-secondary">
          Вернуться на главную
        </Link>
      </div>
    );
  }

  return (
    <div className="stack-lg">
      <Link to="/" className="btn btn-link">
        ← Вернуться к списку
      </Link>

      <article className="card">
        <header>
          <h1>{news.title}</h1>
          <p className="muted">
            {dayjs(news.publication_date).format("DD.MM.YYYY HH:mm")} • Автор: #{news.author_id}
          </p>
        </header>
        <div className="news-content">
          <p>
            {typeof news.content === "string"
              ? news.content
              : (news.content as Record<string, unknown>)?.body ??
                (news.content as Record<string, unknown>)?.text ??
                JSON.stringify(news.content, null, 2)}
          </p>
          {news.cover && <img src={news.cover} alt={news.title} className="news-cover" />}
        </div>
        {canManageCurrentNews && (
          <div className="card-actions">
            <Link to={`/edit-news/${news.id}`} className="btn btn-secondary">
              Редактировать
            </Link>
            <button type="button" className="btn btn-danger" onClick={handleDeleteNews}>
              Удалить
            </button>
          </div>
        )}
      </article>

      <section className="stack-sm">
        <header className="section-head">
          <div>
            <h2>Комментарии</h2>
            <p className="muted">Обсуждение новости.</p>
          </div>
          {commentError && <p className="error">{commentError}</p>}
        </header>
        {user ? (
          <CommentForm submitLabel="Добавить комментарий" onSubmit={handleCreateComment} />
        ) : (
          <p>
            Чтобы комментировать, <Link to="/auth">войдите в систему</Link>.
          </p>
        )}
        <CommentList
          comments={comments}
          currentUser={user}
          onUpdate={handleUpdateComment}
          onDelete={handleDeleteComment}
          canManage={(comment) => canManageComment(user, comment)}
        />
      </section>
    </div>
  );
};


