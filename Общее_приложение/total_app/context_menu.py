import tkinter as tk
from tkinter import messagebox

class ContextMenuManager:
    """
    Класс ContextMenuManager управляет контекстным меню таблицы,
    включая операции копирования, вставки и удаления.
    """
    def __init__(self, tree, clipboard_owner, status_var, undo_redo_manager):
        self.tree = tree  # Виджет Treeview
        self.clipboard_owner = clipboard_owner  # Виджет для работы с буфером обмена (обычно корневой Tk)
        self.status_var = status_var  # Переменная для строки состояния
        self.undo_redo_manager = undo_redo_manager  # Менеджер undo/redo

    def copy_selection(self):
        """
        Копирует выделенные строки в буфер обмена.
        """
        selected_items = self.tree.selection()
        if not selected_items:
            return

        copy_data = []
        for item in selected_items:
            values = self.tree.item(item)['values']
            copy_data.append('\t'.join(str(v) for v in values))

        copy_text = '\n'.join(copy_data)

        self.clipboard_owner.clipboard_clear()
        self.clipboard_owner.clipboard_append(copy_text)

        self.status_var.set(f'Скопировано строк: {len(selected_items)}')

    def paste_selection(self):
        """
        Вставляет данные из буфера обмена в таблицу.
        """
        try:
            clipboard_data = self.clipboard_owner.clipboard_get()
            rows = clipboard_data.split('\n')
            selected_items = self.tree.selection()

            if not selected_items:
                for row in rows:
                    values = row.split('\t')
                    self.tree.insert('', tk.END, values=values)
            else:
                for item, row in zip(selected_items, rows):
                    values = row.split('\t')
                    current_values = list(self.tree.item(item)['values'])

                    self.undo_redo_manager.add_undo_action({
                        'item': item,
                        'column': 'all',
                        'old_value': current_values,
                        'new_value': values
                    })

                    self.tree.item(item, values=values)

            self.status_var.set('Данные вставлены')

        except tk.TclError:
            self.status_var.set('Буфер обмена пуст')

    def delete_selection(self):
        """
        Удаляет выделенные строки из таблицы с подтверждением.
        """
        selected_items = self.tree.selection()
        if not selected_items:
            return

        if messagebox.askyesno("Подтверждение",
                               f"Удалить выбранные строки ({len(selected_items)})?"):
            deleted_data = []
            for item in selected_items:
                values = self.tree.item(item)['values']
                deleted_data.append((item, values))
                self.tree.delete(item)

            self.undo_redo_manager.add_undo_action({
                'action': 'delete',
                'data': deleted_data
            })

            self.status_var.set(f'Удалено строк: {len(selected_items)}')
