using System;
using System.Collections.Generic;
using System.Linq;
using CollabTodoDesktop.Models;

namespace CollabTodoDesktop.Services;

/// <summary>
/// 대시보드에서 사용할 간단한 통계 계산 서비스
/// Python 버전의 summarize_tasks 함수와 동일한 기능
/// </summary>
public class DashboardService : IDashboardService
{
    public TaskSummary SummarizeTasks(List<Task> tasks, DateTime now)
    {
        var total = tasks.Count;
        var pending = 0;
        var inProgress = 0;
        var review = 0;
        var onHold = 0;
        var completed = 0;
        var cancelled = 0;
        var dueSoon = 0;
        var overdue = 0;

        var soonThreshold = now.AddDays(1);

        foreach (var task in tasks)
        {
            switch (task.Status)
            {
                case TaskStatus.Pending:
                    pending++;
                    break;
                case TaskStatus.InProgress:
                    inProgress++;
                    break;
                case TaskStatus.Review:
                    review++;
                    break;
                case TaskStatus.OnHold:
                    onHold++;
                    break;
                case TaskStatus.Completed:
                    completed++;
                    break;
                case TaskStatus.Cancelled:
                    cancelled++;
                    break;
            }

            if (task.DueDate.HasValue && 
                task.Status != TaskStatus.Completed && 
                task.Status != TaskStatus.Cancelled)
            {
                if (task.DueDate.Value < now)
                {
                    overdue++;
                }
                else if (task.DueDate.Value <= soonThreshold)
                {
                    dueSoon++;
                }
            }
        }

        return new TaskSummary
        {
            Total = total,
            Pending = pending,
            InProgress = inProgress,
            Review = review,
            OnHold = onHold,
            Completed = completed,
            Cancelled = cancelled,
            DueSoon = dueSoon,
            Overdue = overdue
        };
    }
}

