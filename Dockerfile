# Use the official Apache Airflow image as the base
FROM apache/airflow:2.10.3

# Set environment variables for Airflow version and Python version
ENV AIRFLOW_VERSION=2.10.3
ENV PYTHON_VERSION=3.12.7

# Set up the constraints URL for dependencies
ENV CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# Set the Airflow home directory (optional)
ENV AIRFLOW_HOME=/opt/airflow

# Ensure the container uses the airflow user
USER airflow

# Set the working directory to where the DAGs are located
WORKDIR /opt/airflow/dags

# Copy your DAGs (and other project files) into the container (optional)
COPY dags/ /opt/airflow/dags/

# Expose the necessary port (Airflow Web Server)
EXPOSE 8080

# Set the default command to run Airflow Web Server, Scheduler, etc.
CMD ["bash", "-c", "airflow webserver & airflow scheduler"]
