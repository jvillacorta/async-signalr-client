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

        public async Task RequestMessage(string returnTarget, string name, string message)
        {
            Console.WriteLine("/chat/RequestMessage --> " + name + ", " + message);
            await Clients.Caller.SendAsync(returnTarget, name, message);
        }

        public async Task RequestBroadcast(string returnTarget, string message)
        {
            Console.WriteLine("/chat/RequestBroadcast --> " + message);
            await Clients.All.SendAsync(returnTarget, message);
        }

        public async Task RequestInvokeString(string returnTarget, string sample)
        {
            Console.WriteLine("/chat/RequestInvokeString --> " + sample);
            await Clients.Caller.SendAsync(returnTarget, sample);
        }

        public async Task RequestInvokeInteger(string returnTarget, int sample)
        {
            Console.WriteLine("/chat/RequestInvokeInteger --> " + sample);
            await Clients.Caller.SendAsync(returnTarget, sample);
        }

        public async Task RequestInvokeFloat(string returnTarget, float sample)
        {
            Console.WriteLine("/chat/RequestInvokeFloat --> " + sample);
            await Clients.Caller.SendAsync(returnTarget, sample);
        }

        public async Task RequestInvokeStringArray(string returnTarget, string[] sample)
        {
            Console.WriteLine("/chat/RequestInvokeStringArray --> " + sample);
            await Clients.Caller.SendAsync(returnTarget, sample);
        }

    }
}
