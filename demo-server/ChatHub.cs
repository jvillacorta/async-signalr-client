using System;
using System.Threading.Tasks;
using Microsoft.AspNetCore.SignalR;

namespace SignalRSimpleChat
{
    public class Chat : Hub
    {
        public async Task<string> InvokeSample(string text, int delay = 500)
        {
            Console.WriteLine("/chat/InvokeSample --> " + text + " Delay: " + delay);
            await Task.Delay(delay);
            return text;
        }

        public async Task SendSample(string text)
        {
            Console.WriteLine("/chat/SendSample --> " + text);
        }
    }
}
