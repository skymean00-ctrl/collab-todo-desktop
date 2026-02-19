using System;
using System.Windows;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using CollabTodoDesktop.Services;
using CollabTodoDesktop.Views;

namespace CollabTodoDesktop
{
    public partial class App : Application
    {
        public IServiceProvider ServiceProvider { get; private set; } = null!;

        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            var config = new ConfigurationBuilder()
                .SetBasePath(System.IO.Directory.GetCurrentDirectory())
                .AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
                .AddJsonFile("appsettings.Development.json", optional: true)
                .AddEnvironmentVariables()
                .Build();

            // API URL: 환경변수 > appsettings.json
            var apiBaseUrl =
                Environment.GetEnvironmentVariable("COLLAB_TODO_API_URL")
                ?? config["Api:BaseUrl"]
                ?? "https://api.skymeanai.com";

            var apiClient = new ApiClient(apiBaseUrl);

            var services = new ServiceCollection();
            services.AddSingleton(apiClient);
            services.AddSingleton<IDashboardService, DashboardService>();
            services.AddHttpClient();

            // AI 요약 (선택, 설정 없으면 null)
            var configManager = new Configuration.ConfigurationManager(config);
            var aiConfig = configManager.LoadAiServiceConfig();
            if (aiConfig != null)
            {
                services.AddSingleton(aiConfig);
                services.AddScoped<IAiClientService, AiClientService>(
                    sp => new AiClientService(aiConfig,
                        sp.GetRequiredService<System.Net.Http.IHttpClientFactory>()));
            }

            ServiceProvider = services.BuildServiceProvider();

            // 로그인 창 먼저 표시
            var loginWindow = new LoginWindow(apiClient);
            if (loginWindow.ShowDialog() != true)
            {
                Shutdown();
                return;
            }

            // 로그인 성공 → 메인 창
            var mainWindow = new MainWindow();
            MainWindow = mainWindow;
            mainWindow.Show();
        }
    }
}
