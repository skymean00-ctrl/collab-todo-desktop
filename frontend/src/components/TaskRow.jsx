import { useNavigate } from 'react-router-dom'

const PRIORITY_BADGE = {
  urgent: { label: '긴급', cls: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400' },
  high:   { label: '높음', cls: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-400' },
  normal: { label: '보통', cls: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400' },
  low:    { label: '낮음', cls: 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400' },
}

const STATUS_BADGE = {
  pending:     { label: '대기',     cls: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300' },
  in_progress: { label: '진행중',   cls: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400' },
  review:      { label: '검토요청', cls: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400' },
  approved:    { label: '완료',     cls: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' },
  rejected:    { label: '반려',     cls: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400' },
}

function isOverdue(due_date, status) {
  if (!due_date || status === 'approved') return false
  return new Date(due_date) < new Date()
}

export default function TaskRow({ task, showAssigner = false, showAssignee = false }) {
  const navigate = useNavigate()
  const priority = PRIORITY_BADGE[task.priority] || PRIORITY_BADGE.normal
  const status = STATUS_BADGE[task.status] || STATUS_BADGE.pending
  const overdue = isOverdue(task.due_date, task.status)

  return (
    <tr
      className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700"
      onClick={() => navigate(`/tasks/${task.id}`)}
    >
      {/* 제목 */}
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-800 dark:text-gray-100">{task.title}</span>
          {task.subtask_count > 0 && (
            <span className="text-xs bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 px-1.5 py-0.5 rounded">
              자료요청 {task.subtasks_done}/{task.subtask_count}
            </span>
          )}
          {task.attachment_count > 0 && (
            <span className="text-xs text-gray-400">📎 {task.attachment_count}</span>
          )}
        </div>
        {task.category && (
          <span className="text-xs px-1.5 py-0.5 rounded mt-0.5 inline-block"
            style={{ backgroundColor: task.category.color + '33', color: task.category.color }}>
            {task.category.name}
          </span>
        )}
      </td>

      {/* 담당자 or 지시자 */}
      {showAssignee && (
        <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-300">{task.assignee?.name}</td>
      )}
      {showAssigner && (
        <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-300">{task.assigner?.name}</td>
      )}

      {/* 우선순위 */}
      <td className="py-3 px-4">
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${priority.cls}`}>
          {priority.label}
        </span>
      </td>

      {/* 상태 */}
      <td className="py-3 px-4">
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${status.cls}`}>
          {status.label}
        </span>
      </td>

      {/* 진행률 */}
      <td className="py-3 px-4 w-28">
        <div className="flex items-center gap-1.5">
          <div className="flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
            <div
              className="bg-primary-500 h-1.5 rounded-full transition-all"
              style={{ width: `${task.progress}%` }}
            />
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-400 w-8">{task.progress}%</span>
        </div>
      </td>

      {/* 마감일 */}
      <td className="py-3 px-4 text-sm">
        {task.due_date ? (
          <span className={overdue ? 'text-red-600 dark:text-red-400 font-medium' : 'text-gray-600 dark:text-gray-300'}>
            {overdue && '⚠ '}{task.due_date}
          </span>
        ) : (
          <span className="text-gray-300 dark:text-gray-600">-</span>
        )}
      </td>
    </tr>
  )
}
