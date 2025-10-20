from cmd import PROMPT
from click import confirmation_option, prompt
import typer
import uuid
from rich.console import Console
from rich.table import Table
from typing import Literal
from rich import print
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
def list(UUID, name, description, status,):
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
def update(uuid_task: str):
    """Update a task's name, description or status"""
    conn = connect_database("./src/database/todo.db")
    cursor = conn.cursor()

    cursor.execute("SELECT uuid, name, description, status FROM tasks WHERE uuid = ?", (uuid_task,))
    task = cursor.fetchone()

    if not task:
        print("[bold red] Task not found[/bold red]")
        conn.close()
        return

    print(f"[bold cyan]Editing Task:[/bold cyan] {task[1]}")

    new_name = prompt.ask("Enter new name", default=task[1])
    new_description = PROMPT.ask("Enter new description", default=task[2])
    new_status = prompt.ask("Enter new status [COMPLETED, PENDING, IN_PROGRESS]", default=task[3])

    cursor.execute("""
        UPDATE tasks
        SET name = ?, description = ?, status = ?
        WHERE uuid = ?
    """, (new_name, new_description, new_status, uuid_task))

    conn.commit()
    conn.close()

    print("[bold green] Task updated successfully![/bold green]")
    list()


@app.command(short_help="Delete one task")
def delete(uuid_task: str):
    """Delete a task"""
    conn = connect_database("./src/database/todo.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM tasks WHERE uuid = ?", (uuid_task,))
    task = cursor.fetchone()

    if not task:
        print("[bold red] Task not found[/bold red]")
        conn.close()
        return

    confirm = confirmation_option.ask(f"Are you sure you want to delete task '{task[0]}'?")
    if not confirm:
        print("[bold yellow] Task deletion canceled[/bold yellow]")
        conn.close()
        return

    cursor.execute("DELETE FROM tasks WHERE uuid = ?", (uuid_task,))
    conn.commit()
    conn.close()

    print("[bold green]✔ Task deleted successfully![/bold green]")
    list()

    