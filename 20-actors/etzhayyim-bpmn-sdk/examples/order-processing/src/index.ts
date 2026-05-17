// Merkle DAG: order_processing_example
// Order Processing Workflow Example - Complete Business Process

import { flow } from '@gftd/bpmn-sdk/dsl';
import { compileToXml } from '@gftd/bpmn-sdk/compiler';
import { BpmnRuntime } from '@gftd/bpmn-sdk/runtime';
import { validateProcess } from '@gftd/bpmn-sdk/validation';
import { HumanTaskManager } from '@gftd/bpmn-sdk/human';
import { BpmnMonitor } from '@gftd/bpmn-sdk/ops';
import { bpmnPropertyTest, bpmnScenarioTest } from '@gftd/bpmn-sdk/testing';

/**
 * Complete Order Processing Workflow
 *
 * Order Received → Validate Order → Check Stock → Payment Processing → Shipping
 *                        ↓              ↓              ↓
 *                   Validation Error  Out of Stock   Payment Failed
 *                        ↓              ↓              ↓
 *                   Send Error Email  Notify Customer Send Error Email
 */

async function createOrderProcessingWorkflow() {
  return flow('OrderProcessingWorkflow', f => f
    .process('OrderProcessingWorkflow', p => {
      // === 開始イベント ===
      p.startEvent('OrderReceived')
        .name('注文受付')
        .message('orderMessage');

      // === 注文検証 ===
      p.serviceTask('ValidateOrder')
        .name('注文内容検証')
        .implementation('orderValidationService');

      // === 在庫チェック ===
      p.serviceTask('CheckInventory')
        .name('在庫確認')
        .implementation('inventoryCheckService');

      // === 条件分岐: 金額ベース ===
      p.exclusiveGateway('AmountCheck')
        .name('注文金額チェック');

      // === 高額注文: 承認フロー ===
      p.userTask('ManagerApproval')
        .name('マネージャー承認')
        .assignee('${managerId}')
        .dueDate('${approvalDeadline}');

      // === 通常注文: 自動処理 ===
      p.serviceTask('AutoApproval')
        .name('自動承認')
        .implementation('autoApprovalService');

      // === 支払い処理 ===
      p.serviceTask('ProcessPayment')
        .name('支払い処理')
        .implementation('paymentService');

      // === 配送準備 ===
      p.userTask('PrepareShipping')
        .name('配送準備')
        .candidateGroups(['warehouse'])
        .dueDate('${shippingDeadline}');

      // === 配送 ===
      p.serviceTask('ShipOrder')
        .name('注文配送')
        .implementation('shippingService');

      // === 完了 ===
      p.endEvent('OrderCompleted')
        .name('注文完了');

      // === エラー処理 ===
      p.boundaryEvent('ValidationError')
        .attachedToRef('ValidateOrder')
        .error('validationError')
        .name('検証エラー');

      p.boundaryEvent('OutOfStock')
        .attachedToRef('CheckInventory')
        .signal('outOfStockSignal')
        .name('在庫不足');

      p.boundaryEvent('PaymentFailed')
        .attachedToRef('ProcessPayment')
        .error('paymentError')
        .name('支払い失敗');

      // エラーハンドリングタスク
      p.serviceTask('SendErrorEmail')
        .name('エラーメール送信')
        .implementation('errorEmailService');

      p.serviceTask('NotifyCustomer')
        .name('顧客通知')
        .implementation('customerNotificationService');

      // === シーケンスフロー ===

      // メインフロー
      p.sequenceFlow('OrderReceived', 'ValidateOrder');
      p.sequenceFlow('ValidateOrder', 'CheckInventory');
      p.sequenceFlow('CheckInventory', 'AmountCheck');

      // 金額分岐
      p.sequenceFlow('AmountCheck', 'ManagerApproval')
        .condition('${totalAmount > 50000}'); // 5万円以上は承認が必要

      p.sequenceFlow('AmountCheck', 'AutoApproval')
        .condition('${totalAmount <= 50000}');

      // 承認後の処理
      p.sequenceFlow('ManagerApproval', 'ProcessPayment');
      p.sequenceFlow('AutoApproval', 'ProcessPayment');

      // 配送処理
      p.sequenceFlow('ProcessPayment', 'PrepareShipping');
      p.sequenceFlow('PrepareShipping', 'ShipOrder');
      p.sequenceFlow('ShipOrder', 'OrderCompleted');

      // エラーハンドリング
      p.sequenceFlow('ValidationError', 'SendErrorEmail');
      p.sequenceFlow('OutOfStock', 'NotifyCustomer');
      p.sequenceFlow('PaymentFailed', 'SendErrorEmail');

      p.sequenceFlow('SendErrorEmail', 'OrderCompleted');
      p.sequenceFlow('NotifyCustomer', 'OrderCompleted');
    })
  );
}

/**
 * Order Processing Service Implementations
 */
class OrderProcessingServices {
  static async validateOrder(orderData: any): Promise<any> {
    console.log('🔍 Validating order:', orderData.orderId);

    // 基本検証
    if (!orderData.customerId || !orderData.items || orderData.items.length === 0) {
      throw new Error('Invalid order: missing required fields');
    }

    // 金額計算
    const totalAmount = orderData.items.reduce((sum: number, item: any) =>
      sum + (item.price * item.quantity), 0
    );

    return {
      ...orderData,
      totalAmount,
      validationStatus: 'valid',
      validatedAt: new Date()
    };
  }

  static async checkInventory(orderData: any): Promise<any> {
    console.log('📦 Checking inventory for order:', orderData.orderId);

    // 在庫チェックのシミュレーション
    const outOfStock = orderData.items.some((item: any) => {
      // ランダムに在庫切れをシミュレート (10%の確率)
      return Math.random() < 0.1;
    });

    if (outOfStock) {
      throw new Error('Out of stock');
    }

    return {
      ...orderData,
      inventoryStatus: 'available',
      checkedAt: new Date()
    };
  }

  static async processAutoApproval(orderData: any): Promise<any> {
    console.log('✅ Auto-approving order:', orderData.orderId);

    return {
      ...orderData,
      approvalStatus: 'auto-approved',
      approvedAt: new Date(),
      approvedBy: 'system'
    };
  }

  static async processPayment(orderData: any): Promise<any> {
    console.log('💳 Processing payment for order:', orderData.orderId);

    // 支払い失敗のシミュレーション (5%の確率)
    if (Math.random() < 0.05) {
      throw new Error('Payment failed');
    }

    return {
      ...orderData,
      paymentStatus: 'completed',
      paidAt: new Date(),
      transactionId: `txn_${Date.now()}`
    };
  }

  static async prepareShipping(orderData: any): Promise<any> {
    console.log('📦 Preparing shipping for order:', orderData.orderId);

    return {
      ...orderData,
      shippingStatus: 'prepared',
      preparedAt: new Date(),
      trackingNumber: `TRK${Date.now()}`
    };
  }

  static async shipOrder(orderData: any): Promise<any> {
    console.log('🚚 Shipping order:', orderData.orderId);

    return {
      ...orderData,
      shippingStatus: 'shipped',
      shippedAt: new Date(),
      estimatedDelivery: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000) // 3日後
    };
  }

  static async sendErrorEmail(orderData: any): Promise<any> {
    console.log('📧 Sending error email for order:', orderData.orderId);

    return {
      ...orderData,
      errorEmailSent: true,
      errorEmailSentAt: new Date()
    };
  }

  static async notifyCustomer(orderData: any): Promise<any> {
    console.log('📢 Notifying customer about order:', orderData.orderId);

    return {
      ...orderData,
      customerNotified: true,
      customerNotifiedAt: new Date()
    };
  }
}

/**
 * Run Complete Order Processing Demo
 */
async function runOrderProcessingDemo() {
  console.log('🛒 Starting Order Processing Workflow Demo...\n');

  let runtime: BpmnRuntime;
  let taskManager: HumanTaskManager;
  let monitor: BpmnMonitor | undefined;

  try {
    // ==========================================
    // 1. WORKFLOW MODELING & VALIDATION
    // ==========================================
    console.log('📝 Step 1: Workflow Modeling & Validation');

    const orderWorkflow = await createOrderProcessingWorkflow();
    console.log('✅ Order processing workflow created');

    // Validate workflow
    const validation = await validateProcess(orderWorkflow);
    console.log(`✅ Workflow validation: ${validation.valid ? 'PASSED' : 'FAILED'}`);
    console.log(`   - Complexity Score: ${validation.statistics.complexityScore}`);

    if (!validation.valid) {
      console.error('Validation errors:');
      validation.errors.forEach(error => console.error(`  - ${error.message}`));
      throw new Error('Workflow validation failed');
    }

    // ==========================================
    // 2. SYSTEM SETUP
    // ==========================================
    console.log('\n⚙️  Step 2: System Setup');

    runtime = new BpmnRuntime();
    taskManager = new HumanTaskManager(runtime);

    monitor = new BpmnMonitor({
      serviceName: 'order-processing-service',
      metrics: { enabled: true, interval: 10000 },
      otel: { /* disabled for demo */ },
      logging: { level: 'info', format: 'json', destination: 'console' },
      alerts: {
        enabled: true,
        thresholds: {
          maxProcessInstances: 50,
          maxActiveTasks: 25,
          maxErrorRate: 0.1,
          maxAverageDuration: 30 * 60 * 1000, // 30分
          slaBreachRate: 0.2
        }
      }
    });

    monitor.attachToRuntime(runtime);
    console.log('✅ Systems initialized');

    // ==========================================
    // 3. PROPERTY TESTING
    // ==========================================
    console.log('\n🧪 Step 3: Property Testing');

    const propertyTests = ['noDeadEnds', 'gatewayConsistency', 'properTermination'];
    for (const property of propertyTests) {
      const result = await bpmnPropertyTest(orderWorkflow, runtime, property, {
        maxTestCases: 10,
        timeout: 5000
      });
      console.log(`✅ Property "${property}": ${result.success ? 'PASSED' : 'FAILED'}`);
    }

    // ==========================================
    // 4. PROCESS ORDERS
    // ==========================================
    console.log('\n📦 Step 4: Processing Orders');

    const orders = [
      {
        id: 'ORD-001',
        type: 'low-value',
        customerId: 'CUST-001',
        items: [
          { id: 'ITEM-001', name: 'Laptop', price: 80000, quantity: 1 },
          { id: 'ITEM-002', name: 'Mouse', price: 2000, quantity: 1 }
        ],
        totalAmount: 82000
      },
      {
        id: 'ORD-002',
        type: 'high-value',
        customerId: 'CUST-002',
        items: [
          { id: 'ITEM-003', name: 'Server', price: 200000, quantity: 1 }
        ],
        totalAmount: 200000
      },
      {
        id: 'ORD-003',
        type: 'out-of-stock',
        customerId: 'CUST-003',
        items: [
          { id: 'ITEM-004', name: 'Rare Item', price: 5000, quantity: 1 }
        ],
        totalAmount: 5000
      }
    ];

    for (const order of orders) {
      console.log(`\n🎯 Processing Order: ${order.id} (${order.type})`);

      try {
        // Deploy and start process
        const context = await runtime.startInstance(
          await runtime.deployProcess(orderWorkflow, `OrderProcess-${order.id}`),
          {
            instanceId: `instance-${order.id}`,
            variables: {
              orderId: order.id,
              customerId: order.customerId,
              items: order.items,
              totalAmount: order.totalAmount,
              managerId: 'manager@example.com',
              approvalDeadline: new Date(Date.now() + 24 * 60 * 60 * 1000),
              shippingDeadline: new Date(Date.now() + 48 * 60 * 60 * 1000)
            },
            businessKey: order.id
          }
        );

        console.log(`✅ Order process started: ${context.instanceId}`);

        // Wait for completion or manual intervention
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Check for pending tasks
        const pendingTasks = taskManager.getTasksForUser('manager@example.com');
        if (pendingTasks.length > 0) {
          console.log('📋 Found approval task, processing...');

          const approvalTask = pendingTasks[0];
          if (approvalTask) {
            await taskManager.claimTask(approvalTask.id, 'manager@example.com');
            await taskManager.completeTask(approvalTask.id, 'manager@example.com', {
            approved: true,
            approvalDate: new Date(),
            comments: 'High-value order approved'
          });
          }
          console.log('✅ Approval task completed');
        }

        // Check warehouse tasks
        const warehouseTasks = taskManager.getTasksForUser('warehouse-user@example.com');
        if (warehouseTasks.length > 0) {
          console.log('📦 Found shipping task, processing...');

          const shippingTask = warehouseTasks[0];
          if (shippingTask) {
            await taskManager.claimTask(shippingTask.id, 'warehouse-user@example.com');
            await taskManager.completeTask(shippingTask.id, 'warehouse-user@example.com', {
            prepared: true,
            preparationDate: new Date(),
            notes: 'Order prepared for shipping'
          });
          }
          console.log('✅ Shipping task completed');
        }

        // Wait for final completion
        await new Promise(resolve => setTimeout(resolve, 2000));

        const finalContext = await runtime.getExecutionContext('', context.instanceId);
        console.log(`✅ Order ${order.id} completed: ${finalContext?.status}`);

      } catch (error) {
        console.log(`❌ Order ${order.id} failed:`, error instanceof Error ? error.message : 'Unknown error');
      }
    }

    // ==========================================
    // 5. MONITORING REPORT
    // ==========================================
    console.log('\n📊 Step 5: Monitoring Report');

    const snapshot = await monitor.getPerformanceSnapshot();
    console.log('📈 Performance Metrics:');
    console.log(`   - Total Instances: ${snapshot.metrics.totalInstances}`);
    console.log(`   - Completed: ${snapshot.metrics.completedInstances}`);
    console.log(`   - Failed: ${snapshot.metrics.failedInstances}`);
    console.log(`   - Active Tasks: ${snapshot.metrics.activeTasks}`);
    console.log(`   - Average Duration: ${Math.round(snapshot.metrics.averageDuration)}ms`);

    const health = await monitor.getHealthStatus();
    console.log(`🏥 System Health: ${health.status}`);

    const alerts = monitor.getAlerts();
    console.log(`🚨 Active Alerts: ${alerts.length}`);

    // ==========================================
    // 6. FINAL SUMMARY
    // ==========================================
    console.log('\n🎉 Order Processing Demo Completed!');
    console.log('\n📋 Summary:');
    console.log('✅ Complex workflow with error handling');
    console.log('✅ Human task management with SLAs');
    console.log('✅ Multiple execution paths');
    console.log('✅ Comprehensive monitoring');
    console.log('✅ Property-based validation');
    console.log('✅ Real-world business logic integration');

    console.log('\n🚀 BPMN SDK successfully demonstrated complete order processing workflow!');

  } catch (error) {
    console.error('\n❌ Demo failed:', error);
    console.error('Stack trace:', error instanceof Error ? error.stack : 'No stack trace');

    if (monitor !== undefined) {
      await monitor.shutdown().catch(console.error);
    }

    process.exit(1);
  }
}

// Export for testing
export { createOrderProcessingWorkflow, OrderProcessingServices, runOrderProcessingDemo };

// Run demo
if (require.main === module) {
  runOrderProcessingDemo().catch(console.error);
}
