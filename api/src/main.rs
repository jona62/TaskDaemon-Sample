use axum::{
    extract::Path,
    http::header,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use base64::{engine::general_purpose::STANDARD, Engine};
use serde::{Deserialize, Serialize};
use std::env;

#[derive(Deserialize)]
struct ResizeRequest {
    image_url: String,
    width: u32,
    height: u32,
}

#[derive(Deserialize)]
struct ThumbnailRequest {
    image_url: String,
    size: u32,
}

#[derive(Serialize)]
struct QueueResponse {
    task_id: String,
}

#[derive(Serialize)]
struct TaskRequest {
    #[serde(rename = "type")]
    task_type: String,
    data: serde_json::Value,
}

async fn queue_task(task_type: &str, data: serde_json::Value) -> Result<String, String> {
    let daemon_url = env::var("TASKDAEMON_URL").unwrap_or_else(|_| "http://localhost:3000".into());
    let client = reqwest::Client::new();

    let resp = client
        .post(format!("{}/queue", daemon_url))
        .json(&TaskRequest { task_type: task_type.into(), data })
        .send()
        .await
        .map_err(|e| e.to_string())?;

    let body: serde_json::Value = resp.json().await.map_err(|e| e.to_string())?;
    Ok(body["task_id"].as_str().unwrap_or("").to_string())
}

async fn resize(Json(req): Json<ResizeRequest>) -> Json<QueueResponse> {
    let data = serde_json::json!({
        "image_url": req.image_url,
        "width": req.width,
        "height": req.height
    });
    let task_id = queue_task("resize", data).await.unwrap_or_default();
    Json(QueueResponse { task_id })
}

async fn thumbnail(Json(req): Json<ThumbnailRequest>) -> Json<QueueResponse> {
    let data = serde_json::json!({
        "image_url": req.image_url,
        "size": req.size
    });
    let task_id = queue_task("thumbnail", data).await.unwrap_or_default();
    Json(QueueResponse { task_id })
}

async fn get_task(Path(task_id): Path<String>) -> Json<serde_json::Value> {
    let daemon_url = env::var("TASKDAEMON_URL").unwrap_or_else(|_| "http://localhost:3000".into());
    let client = reqwest::Client::new();

    let resp = match client
        .get(format!("{}/api/tasks/{}", daemon_url, task_id))
        .send()
        .await
    {
        Ok(r) => r.json().await.unwrap_or(serde_json::json!({"error": "parse error"})),
        Err(_) => serde_json::json!({"error": "not found"}),
    };

    Json(resp)
}

async fn get_image(Path(task_id): Path<String>) -> impl IntoResponse {
    let daemon_url = env::var("TASKDAEMON_URL").unwrap_or_else(|_| "http://localhost:3000".into());
    let client = reqwest::Client::new();

    let resp: serde_json::Value = match client
        .get(format!("{}/api/tasks/{}", daemon_url, task_id))
        .send()
        .await
    {
        Ok(r) => r.json().await.unwrap_or_default(),
        Err(_) => return (axum::http::StatusCode::NOT_FOUND, "Task not found").into_response(),
    };

    if resp["status"] != "completed" {
        return (axum::http::StatusCode::NOT_FOUND, "Task not completed").into_response();
    }

    let b64 = resp["result"]["data"].as_str().unwrap_or("");
    match STANDARD.decode(b64) {
        Ok(data) => ([(header::CONTENT_TYPE, "image/png")], data).into_response(),
        Err(_) => (axum::http::StatusCode::INTERNAL_SERVER_ERROR, "Invalid image data").into_response(),
    }
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/resize", post(resize))
        .route("/thumbnail", post(thumbnail))
        .route("/tasks/:id", get(get_task))
        .route("/images/:task_id", get(get_image));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080").await.unwrap();
    println!("API listening on http://0.0.0.0:8080");
    axum::serve(listener, app).await.unwrap();
}
