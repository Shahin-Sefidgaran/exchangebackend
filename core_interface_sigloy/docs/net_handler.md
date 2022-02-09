### **Network Handler**

This is the most important part of "**Interface**". This part has multiple section to handle all incoming request(from
client to the **core**):

- **Interface Api Endpoint:** This part is responsible to get incoming request and send them to producer and wait for
  the answer for a specific time("timed out" in the settings file).
- **Producer:** This part send all incoming requests into the redis queue to be consumed later.
- **Redis Queue:** This part gets items from redis queue and puts them into the "internal python priority queue".
- **Priority Item:** This is a specific item that has been made to do some special operation while comparing to other
  items in the python's built-in heap priority queue. for example in all comparing times, it will refresh the priority
  of the item depends on elapsed time in the queue.
- **Consumer:** This part get items from the internal priority queue and pass them to the "RequestWrapper" and finally
  to the "Interface" class.
- **Interface Class:** This part send requests to the core with required arguments and return the received response.

All these parts make life cycle of a request from client(other servers) to the core and vice versa.

