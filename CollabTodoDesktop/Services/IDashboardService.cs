using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using CollabTodoDesktop.Models;

namespace CollabTodoDesktop.Services;

/// <summary>
/// 대시보드 서비스 인터페이스
/// </summary>
public interface IDashboardService
{
    /// <summary>
    /// 작업 목록에 대한 간단한 집계를 수행합니다.
    /// </summary>
    TaskSummary SummarizeTasks(List<Task> tasks, DateTime now);
}

