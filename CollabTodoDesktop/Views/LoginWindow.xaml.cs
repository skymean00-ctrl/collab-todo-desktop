using System.Windows;
using System.Windows.Input;
using CollabTodoDesktop.Services;

namespace CollabTodoDesktop.Views;

public partial class LoginWindow : Window
{
    private readonly ApiClient _api;

    public LoginWindow(ApiClient api)
    {
        InitializeComponent();
        _api = api;
        UsernameBox.Focus();
    }

    private async void OnLogin_Click(object sender, RoutedEventArgs e)
    {
        await TryLoginAsync();
    }

    private async void OnKeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter)
            await TryLoginAsync();
    }

    private async System.Threading.Tasks.Task TryLoginAsync()
    {
        var username = UsernameBox.Text.Trim();
        var password = PasswordBox.Password;

        if (string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
        {
            ShowError("아이디와 비밀번호를 입력하세요.");
            return;
        }

        LoginButton.IsEnabled = false;
        LoginButton.Content = "로그인 중...";
        ErrorText.Visibility = Visibility.Collapsed;

        try
        {
            var ok = await _api.LoginAsync(username, password);
            if (ok)
            {
                DialogResult = true;
            }
            else
            {
                ShowError("아이디 또는 비밀번호가 올바르지 않습니다.");
            }
        }
        catch
        {
            ShowError("서버에 연결할 수 없습니다.\napi.skymeanai.com 을 확인하세요.");
        }
        finally
        {
            LoginButton.IsEnabled = true;
            LoginButton.Content = "로그인";
        }
    }

    private void ShowError(string message)
    {
        ErrorText.Text = message;
        ErrorText.Visibility = Visibility.Visible;
    }
}
