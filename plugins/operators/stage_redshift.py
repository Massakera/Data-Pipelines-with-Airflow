from airflow.hooks.postgres_hook import PostgresHook
from airflow.contrib.hooks.aws_hook import AwsHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

class StageToRedshiftOperator(BaseOperator):
    """
        Apache Airflow Operator to Copy source data
        from AWS S3 to AWS Redshift DB.
    """
    ui_color = '#358140'
    template_fields = ("s3_key","execution_date")

    copy_sql_date = """
        COPY {} FROM '{}/{}/{}/'
        ACCESS_KEY_ID '{}'
        SECRET_ACCESS_KEY '{}'
        REGION '{}'
        {} 'auto';
    """

    copy_sql = """
        COPY {} FROM '{}'
        ACCESS_KEY_ID '{}'
        SECRET_ACCESS_KEY '{}'
        REGION '{}'
        {} 'auto';
    """
    
    @apply_defaults
    def __init__(self,
                 # Define operators params (with defaults)
                 redshift_conn_id = "",
                 aws_credentials_id="",
                 table = "",
                 s3_path = "",
                 region= "us-west-2",
                 data_format = "",
                 *args, **kwargs):

        super(StageToRedshiftOperator, self).__init__(*args, **kwargs)

        self.redshift_conn_id = redshift_conn_id
        self.aws_credentials_id = aws_credentials_id
        self.table = table
        self.s3_path = s3_path
        self.region = region
        self.data_format = data_format
        self.execution_date = kwargs.get('execution_date')
        
    def execute(self, context):
        # Set AWS S3 and Redshift connections
        aws_hook = AwsHook(self.aws_credentials_id)
        credentials = aws_hook.get_credentials()
        redshift = PostgresHook(postgres_conn_id=self.redshift_conn_id)
        self.log.info("Deleting data from destination Redshift table")
        redshift.run("DELETE FROM {}".format(self.table))
        self.log.info("Copying data from S3 to Redshift")
        # Backfill a specific date
        if self.execution_date:
            formatted_sql = StageToRedshiftOperator.copy_sql_time.format(
                self.table, 
                self.s3_path, 
                self.execution_date.strftime("%Y"),
                self.execution_date.strftime("%d"),
                credentials.access_key,
                credentials.secret_key, 
                self.region,
                self.data_format,
                self.execution_date
            )
        else:
            formatted_sql = StageToRedshiftOperator.copy_sql.format(
                self.table, 
                self.s3_path, 
                credentials.access_key,
                credentials.secret_key, 
                self.region,
                self.data_format,
                self.execution_date
            )
        redshift.run(formatted_sql)