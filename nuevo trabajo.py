import typer
import uuid
from rich.console import Console
from rich.table import Table
from typing import Literal
from rich import print
from typer import Confirm
from connection.connect_database import connect_database
from helpers.status_colors import status_colored

# Conexión a la base de datos
conn = connect_database("./src/database/todo.db")

app = typer.Typer()
table = Table("UUID", "Name", "Description", "Status", show_lines=True)
console = Console()

STATUS = Literal["COMPLETED", "PENDING", "IN_PROGRESS"]

@app.command(short_help="Create on task")
def create(name: str, description: str, status: STATUS):
  if conn:
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO TASKS(uuid, name, description, status) VALUES(?, ?, ?, ?)",
        (str(uuid.uuid4()), name, description, status, )
    )
    conn.commit()
    conn.close()
    print("One task have been [bold green]created[/bold green]")

@app.command(short_help="List all tasks")
def list():
  if conn:
    cursor = conn.cursor()
    results = cursor.execute(
        "SELECT uuid, name, description, status FROM tasks"
    )
    for uuid, name, description, status in results.fetchall():
      status_with_color = status_colored(status)

      table.add_row(uuid, name, description, status_with_color)
    conn.close()

  table.caption = "List all tasks"
  console.print(table)

@app.command(short_help="Update one task")
def update(
    uuid_: str = typer.Argument(..., help="UUID of the task to update"),
    name: str = typer.Option(None, "--name", "-n", help="New name of the task"),
    description: str = typer.Option(None, "--description", "-d", help="New description of the task"),
    status: STATUS = typer.Option(None, "--status", "-s", help="New status: PENDING, IN_PROGRESS, or COMPLETED")
):
    conn = connect_database("./src/database/todo.db")
    if not conn:
        print("[bold red] Database connection failed[/bold red]")
        return

    cursor = conn.cursor()

    # Verificar si existe la tarea
    cursor.execute("SELECT * FROM TASKS WHERE uuid = ?", (uuid_,))
    if not cursor.fetchone():
        print(f"[bold red] No task found with UUID {uuid_}[/bold red]")
        conn.close()
        return

    # Construir la consulta dinámicamente según los argumentos dados
    fields = []
    values = []

    if name:
        fields.append("name = ?")
        values.append(name)
    if description:
        fields.append("description = ?")
        values.append(description)
    if status:
        fields.append("status = ?")
        values.append(status)

    if not fields:
        print("[yellow] Nothing to update[/yellow]")
        conn.close()
        return

    values.append(uuid_)
    query = f"UPDATE TASKS SET {', '.join(fields)} WHERE uuid = ?"
    cursor.execute(query, tuple(values))
    conn.commit()
    conn.close()
    print("[bold green] Task updated successfully![/bold green]")

@app.command(short_help="Delete one task")
def delete(uuid_: str):
  
    conn = connect_database("./src/database/todo.db")
    if not conn:
        print("[bold red] Database connection failed[/bold red]")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM TASKS WHERE uuid = ?", (uuid_,))
    task = cursor.fetchone()

    if not task:
        print(f"[bold red] No task found with UUID {uuid_}[/bold red]")
        conn.close()
        return

    cursor.execute("DELETE FROM TASKS WHERE uuid = ?", (uuid_,))
    conn.commit()
    conn.close()
    print("[bold green] Task deleted successfully![/bold green]")

if __name__ == "__main__":
    app()
