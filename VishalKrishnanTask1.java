import java.util.Scanner;

public class VishalKrishnanTask1 {
    // Static nested class: power-of-two max heap
    static class PowerOfTwoMaxHeap {
        private int[] heapArray;
        private int currentSize;
        private final int childrenExponent; // Each parent has 2^childrenExponent children
        private final int childrenPerNode;  // Number of children per node

        public PowerOfTwoMaxHeap(int childrenExponent, int capacity) {
            if (childrenExponent < 0) {
                throw new IllegalArgumentException("Exponent must be non-negative.");
            }
            this.childrenExponent = childrenExponent;
            this.childrenPerNode = 1 << childrenExponent;
            this.heapArray = new int[capacity];
            this.currentSize = 0;
        }

        public void insert(int value) {
            if (currentSize == heapArray.length) {
                System.out.println("Heap is full, cannot insert " + value);
                return;
            }
            heapArray[currentSize] = value;
            heapifyUp(currentSize);
            currentSize++;
            System.out.println(value + " inserted.");
        }

        public void popMax() {
            if (currentSize == 0) {
                System.out.println("Heap is empty, cannot pop max.");
                return;
            }
            int maxValue = heapArray[0];
            heapArray[0] = heapArray[--currentSize];
            heapifyDown(0);
            System.out.println("Popped max: " + maxValue);
        }

        private void heapifyUp(int index) {
            int value = heapArray[index];
            while (index > 0) {
                int parentIndex = (index - 1) / childrenPerNode;
                if (heapArray[parentIndex] >= value) break;
                heapArray[index] = heapArray[parentIndex];
                index = parentIndex;
            }
            heapArray[index] = value;
        }

        private void heapifyDown(int index) {
            int value = heapArray[index];
            while (true) {
                int maxChildIndex = -1;
                int maxChildValue = value;
                for (int j = 1; j <= childrenPerNode; j++) {
                    int childIndex = index * childrenPerNode + j;
                    if (childIndex < currentSize && heapArray[childIndex] > maxChildValue) {
                        maxChildValue = heapArray[childIndex];
                        maxChildIndex = childIndex;
                    }
                }
                if (maxChildIndex == -1) break;
                heapArray[index] = maxChildValue;
                index = maxChildIndex;
            }
            heapArray[index] = value;
        }

        public void printHeap() {
            if (currentSize == 0) {
                System.out.println("Heap is empty.");
                return;
            }
            System.out.print("Heap elements: ");
            for (int i = 0; i < currentSize; i++) {
                System.out.print(heapArray[i] + " ");
            }
            System.out.println();
        }
    }

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);

        System.out.print("Enter children exponent (x) for 2^x children per node: ");
        int exponent = scanner.nextInt();

        System.out.print("Enter capacity of the heap: ");
        int capacity = scanner.nextInt();

        PowerOfTwoMaxHeap heap = new PowerOfTwoMaxHeap(exponent, capacity);

        boolean running = true;
        while (running) {
            System.out.println("\nChoose operation:");
            System.out.println("1 - Insert");
            System.out.println("2 - Pop max");
            System.out.println("3 - Print heap");
            System.out.println("4 - Exit");
            System.out.print("Your choice: ");

            int choice = scanner.nextInt();
            switch (choice) {
                case 1:
                    System.out.print("Enter value to insert: ");
                    int val = scanner.nextInt();
                    heap.insert(val);
                    break;
                case 2:
                    heap.popMax();
                    break;
                case 3:
                    heap.printHeap();
                    break;
                case 4:
                    running = false;
                    System.out.println("Exiting.");
                    break;
                default:
                    System.out.println("Invalid choice. Try again.");
            }
        }

        scanner.close();
    }
}

