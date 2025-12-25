use axum::{
    extract::State,
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::env;
use std::sync::Arc;

#[derive(Clone)]
struct AppState {
    daemon_url: String,
    client: reqwest::Client,
}

#[derive(Deserialize)]
struct PrimeRequest {
    limit: u64,
}

#[derive(Serialize, Deserialize)]
struct TaskResponse {
    task_id: String,
}

#[derive(Serialize)]
struct DaemonRequest {
    r#type: String,
    data: serde_json::Value,
}

async fn health() -> &'static str {
    "OK"
}

async fn prime(
    State(state): State<Arc<AppState>>,
    Json(req): Json<PrimeRequest>,
) -> Result<Json<TaskResponse>, StatusCode> {
    let daemon_req = DaemonRequest {
        r#type: "prime".to_string(),
        data: serde_json::json!({ "limit": req.limit }),
    };

    let resp = state
        .client
        .post(format!("{}/queue", state.daemon_url))
        .json(&daemon_req)
        .send()
        .await
        .map_err(|_| StatusCode::BAD_GATEWAY)?;

    let task: TaskResponse = resp.json().await.map_err(|_| StatusCode::BAD_GATEWAY)?;
    Ok(Json(task))
}

#[tokio::main]
async fn main() {
    let daemon_url = env::var("TASKDAEMON_URL").unwrap_or_else(|_| "http://localhost:8080".into());

    let state = Arc::new(AppState {
        daemon_url,
        client: reqwest::Client::new(),
    });

    let app = Router::new()
        .route("/health", get(health))
        .route("/prime", post(prime))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8081").await.unwrap();
    println!("API listening on :8081");
    axum::serve(listener, app).await.unwrap();
}
