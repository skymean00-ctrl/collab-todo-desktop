using System.Collections.Generic;
using System.Linq;
using System.Windows;
using CollabTodoDesktop.Models;

namespace CollabTodoDesktop.Views;

/// <summary>
/// 사용자 선택 다이얼로그
/// Python 버전의 UserSelectionDialog와 동일한 기능
/// </summary>
public partial class UserSelectionDialog : Window
{
    private readonly List<User> _users;
    public User? SelectedUser { get; private set; }

    public UserSelectionDialog(List<User> users)
    {
        InitializeComponent();
        _users = users ?? new List<User>();

        // ComboBox에 사용자 목록 추가
        foreach (var user in _users)
        {
            UserComboBox.Items.Add($"{user.DisplayName} ({user.Username})");
        }

        if (UserComboBox.Items.Count > 0)
        {
            UserComboBox.SelectedIndex = 0;
        }
    }

    private void OkButton_Click(object sender, RoutedEventArgs e)
    {
        var index = UserComboBox.SelectedIndex;
        if (index >= 0 && index < _users.Count)
        {
            SelectedUser = _users[index];
        }
        DialogResult = true;
        Close();
    }

    private void CancelButton_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}

