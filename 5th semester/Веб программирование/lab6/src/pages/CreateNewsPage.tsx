import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { newsApi } from "../api/news";
import { NewsForm, NewsFormValues } from "../components/forms/NewsForm";
import type { NewsItem } from "../types";

export const CreateNewsPage = () => {
  const { id } = useParams();
  const isEditMode = !!id;
  const navigate = useNavigate();

  const [news, setNews] = useState<NewsItem | null>(null);
  const [loading, setLoading] = useState(isEditMode);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isEditMode && id) {
      const loadNews = async () => {
        setLoading(true);
        setError(null);
        try {
          const data = await newsApi.get(Number(id));
          setNews(data);
        } catch (err) {
          console.error(err);
          setError("Не удалось загрузить новость");
        } finally {
          setLoading(false);
        }
      };
      void loadNews();
    }
  }, [id, isEditMode]);

  const getInitialValues = (): NewsFormValues | undefined => {
    if (!news) return undefined;
    const body =
      typeof news.content === "string"
        ? news.content
        : (news.content as Record<string, unknown>)?.body?.toString() ??
          (news.content as Record<string, unknown>)?.text?.toString() ??
          JSON.stringify(news.content);
    return {
      title: news.title,
      body,
      cover: news.cover ?? ""
    };
  };

  const handleSubmit = async (values: NewsFormValues) => {
    setError(null);
    setSubmitting(true);
    try {
      const payload = {
        title: values.title.trim(),
        content: { body: values.body.trim() },
        cover: values.cover?.trim() || undefined
      };

      if (isEditMode && id) {
        await newsApi.update(Number(id), payload);
        navigate(`/news/${id}`);
      } else {
        const created = await newsApi.create(payload);
        navigate(`/news/${created.id}`);
      }
    } catch (err) {
      console.error(err);
      setError("Не удалось сохранить новость. Проверьте права и заполненные поля.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <p>Загрузка данных...</p>
      </div>
    );
  }

  if (error && !news) {
    return (
      <div className="stack-sm">
        <p className="error">{error}</p>
        <button type="button" className="btn btn-secondary" onClick={() => navigate("/")}>
          Вернуться на главную
        </button>
      </div>
    );
  }

  return (
    <div className="stack-lg">
      <section className="card">
        <header className="section-head">
          <div>
            <h1>{isEditMode ? "Редактировать новость" : "Создать новость"}</h1>
            <p className="muted">
              {isEditMode
                ? "Измените заголовок и содержимое новости."
                : "Только верифицированные авторы и администраторы могут публиковать новости."}
            </p>
          </div>
        </header>
        {error && <p className="error">{error}</p>}
        <NewsForm
          initialValues={getInitialValues()}
          submitLabel={isEditMode ? "Сохранить изменения" : "Опубликовать"}
          onSubmit={handleSubmit}
          onCancel={isEditMode ? () => navigate(`/news/${id}`) : undefined}
          disabled={submitting}
        />
      </section>
    </div>
  );
};

