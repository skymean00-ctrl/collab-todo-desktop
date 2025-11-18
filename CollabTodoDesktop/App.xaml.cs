using System;
using System.Windows;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using CollabTodoDesktop.Configuration;

namespace CollabTodoDesktop
{
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application
    {
        public IConfiguration Configuration { get; private set; } = null!;
        public IServiceProvider ServiceProvider { get; private set; } = null!;

        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            // 설정 로드 (appsettings.json + 환경 변수)
            var builder = new ConfigurationBuilder()
                .SetBasePath(System.IO.Directory.GetCurrentDirectory())
                .AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
                .AddJsonFile("appsettings.Development.json", optional: true, reloadOnChange: true)
                .AddEnvironmentVariables();

            Configuration = builder.Build();

            // 의존성 주입 설정
            var serviceCollection = new ServiceCollection();
            ConfigureServices(serviceCollection);
            ServiceProvider = serviceCollection.BuildServiceProvider();
        }

        private void ConfigureServices(IServiceCollection services)
        {
            // Configuration
            services.AddSingleton(Configuration);
            services.AddSingleton<CollabTodoDesktop.Configuration.ConfigurationManager>();
            
            // Load configuration
            var configManager = new CollabTodoDesktop.Configuration.ConfigurationManager(Configuration);
            var dbConfig = configManager.LoadDatabaseConfig();
            var aiConfig = configManager.LoadAiServiceConfig();

            // Register configuration objects
            if (dbConfig != null)
            {
                services.AddSingleton(dbConfig);
            }
            if (aiConfig != null)
            {
                services.AddSingleton(aiConfig);
            }

            // HTTP Client for AI Service
            services.AddHttpClient();
            if (aiConfig != null)
            {
                services.AddScoped<Services.IAiClientService, Services.AiClientService>(
                    sp => new Services.AiClientService(aiConfig, sp.GetRequiredService<System.Net.Http.IHttpClientFactory>()));
            }

            // Repositories
            if (dbConfig != null)
            {
                services.AddScoped<Repositories.IUserRepository, Repositories.UserRepository>(
                    sp => new Repositories.UserRepository(dbConfig));
                services.AddScoped<Repositories.ITaskRepository, Repositories.TaskRepository>(
                    sp => new Repositories.TaskRepository(dbConfig));
                services.AddScoped<Repositories.INotificationRepository, Repositories.NotificationRepository>(
                    sp => new Repositories.NotificationRepository(dbConfig));
            }

            // Services
            services.AddScoped<Services.ISyncService, Services.SyncService>();
            services.AddSingleton<Services.IDashboardService, Services.DashboardService>();
        }
    }
}

