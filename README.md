# AidLogix-Cloud-Native 🛡️📦

AidLogix is a high-availability, cloud-native logistics management system designed for emergency response. It utilizes a decoupled microservices architecture to handle high volumes of aid requests without data loss.

## 🏗️ Architecture
The system is built with a **Producer-Consumer** pattern:
* **Frontend (Bot)**: A Telegram Bot (Python) that receives user requests.
* **Message Queue (SQS)**: AWS SQS serves as a buffer to ensure reliability and fault tolerance.
* **Backend (Worker)**: A Python-based worker that processes messages asynchronously.
* **Database (DynamoDB)**: Persistent NoSQL storage for all logistics data.
* **Infrastructure**: Fully provisioned via Terraform (IaC).
* **Orchestration**: Deployed on Kubernetes (K8s) for scalability.

---

## 🛠️ Tools & Prerequisites
Before running the project, ensure you have the following installed:
* **AWS CLI**: Configured with your credentials.
* **Terraform**: Version 1.7.0 or higher.
* **Docker**: To build application images.
* **Kubectl**: To manage the Kubernetes cluster.
* **Telegram Bot Token**: Obtainable via [@BotFather](https://t.me/botfather).

---

## 🚀 How to Run

### 1. Provision Infrastructure (AWS)
Navigate to the `tf/` directory and run Terraform to create the VPC, SQS, and DynamoDB:
```bash
cd tf
terraform init
terraform apply --auto-approve
