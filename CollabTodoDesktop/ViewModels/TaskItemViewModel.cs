using System;
using System.Windows.Media;
using Models = CollabTodoDesktop.Models;

namespace CollabTodoDesktop.ViewModels;

/// <summary>
/// Task 목록 한 행(row)을 담는 ViewModel
/// </summary>
public class TaskItemViewModel
{
    public int Id { get; }
    public string Title { get; }
    public string StatusText { get; }
    public Brush StatusColor { get; }
    public string DueDateText { get; }
    public Brush DueDateColor { get; }
    public bool IsOverdue { get; }

    public TaskItemViewModel(Models.Task task, DateTime now)
    {
        Id = task.Id;
        Title = task.Title;

        (StatusText, StatusColor) = GetStatusDisplay(task.Status);
        (DueDateText, DueDateColor, IsOverdue) = GetDueDateDisplay(task.DueDate, task.Status, now);
    }

    private static (string text, Brush color) GetStatusDisplay(Models.TaskStatus status)
    {
        return status switch
        {
            Models.TaskStatus.Pending    => ("대기",   new SolidColorBrush(Color.FromRgb(108, 117, 125))),
            Models.TaskStatus.InProgress => ("진행 중", new SolidColorBrush(Color.FromRgb(0,   123, 255))),
            Models.TaskStatus.Review     => ("검토",   new SolidColorBrush(Color.FromRgb(255, 193,   7))),
            Models.TaskStatus.OnHold     => ("보류",   new SolidColorBrush(Color.FromRgb(253, 126,  20))),
            Models.TaskStatus.Completed  => ("완료",   new SolidColorBrush(Color.FromRgb( 40, 167,  69))),
            Models.TaskStatus.Cancelled  => ("취소",   new SolidColorBrush(Color.FromRgb(220,  53,  69))),
            _                            => ("알 수 없음", Brushes.Gray)
        };
    }

    private static (string text, Brush color, bool isOverdue) GetDueDateDisplay(
        DateTime? dueDate, Models.TaskStatus status, DateTime now)
    {
        if (!dueDate.HasValue)
            return ("-", Brushes.Gray, false);

        var isDone = status is Models.TaskStatus.Completed or Models.TaskStatus.Cancelled;
        if (isDone)
            return (dueDate.Value.ToString("MM/dd"), Brushes.Gray, false);

        var diff = (dueDate.Value.Date - now.Date).Days;

        if (diff < 0)
            return ($"D+{-diff} 초과", new SolidColorBrush(Color.FromRgb(220, 53, 69)), true);
        if (diff == 0)
            return ("D-day", new SolidColorBrush(Color.FromRgb(220, 53, 69)), false);
        if (diff <= 3)
            return ($"D-{diff}", new SolidColorBrush(Color.FromRgb(255, 193, 7)), false);

        return ($"D-{diff}", Brushes.DarkGray, false);
    }
}
