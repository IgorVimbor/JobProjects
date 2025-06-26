class UndoRedoManager:
    """
    Класс UndoRedoManager управляет стеком отмены и повтора действий.
    """
    def __init__(self):
        self.undo_stack = []  # Стек для отмены
        self.redo_stack = []  # Стек для повтора

    def add_undo_action(self, action):
        """
        Добавляет действие в стек undo и очищает redo стек.
        """
        self.undo_stack.append(action)
        self.redo_stack.clear()

    def undo(self, tree):
        """
        Выполняет отмену последнего действия, обновляя виджет tree.
        """
        if not self.undo_stack:
            return

        action = self.undo_stack.pop()
        self.redo_stack.append({
            'item': action['item'],
            'column': action['column'],
            'old_value': tree.set(action['item'], action['column']),
            'new_value': action['old_value']
        })

        tree.set(action['item'], action['column'], action['old_value'])

    def redo(self, tree):
        """
        Выполняет повтор последнего отмененного действия, обновляя виджет tree.
        """
        if not self.redo_stack:
            return

        action = self.redo_stack.pop()
        self.undo_stack.append({
            'item': action['item'],
            'column': action['column'],
            'old_value': tree.set(action['item'], action['column']),
            'new_value': action['new_value']
        })

        tree.set(action['item'], action['column'], action['new_value'])

    def clear(self):
        """
        Очищает стеки undo и redo.
        """
        self.undo_stack.clear()
        self.redo_stack.clear()

    def can_undo(self):
        """
        Проверяет, есть ли действия для отмены.
        """
        return bool(self.undo_stack)

    def can_redo(self):
        """
        Проверяет, есть ли действия для повтора.
        """
        return bool(self.redo_stack)
