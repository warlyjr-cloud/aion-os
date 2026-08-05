package com.aionos.edgenode.ui

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.Typeface
import android.os.Build
import android.os.Bundle
import android.os.IBinder
import android.text.InputType
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.cardview.widget.CardView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.aionos.edgenode.R
import com.aionos.edgenode.model.PoStState
import com.aionos.edgenode.model.PoStStatus
import com.aionos.edgenode.service.PoStDaemonService
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import java.util.Locale

/**
 * Main Activity UI binding to [PoStDaemonService], displaying node status,
 * RAM allocation controls, real-time hardware metrics, and proof status.
 */
class MainActivity : AppCompatActivity() {

    private var daemonService: PoStDaemonService? = null
    private var isBound = false
    private var observationJob: Job? = null

    private lateinit var tvStatus: TextView
    private lateinit var etRam: EditText
    private lateinit var etIterations: EditText
    private lateinit var btnStart: Button
    private lateinit var btnCancel: Button
    private lateinit var progressBar: ProgressBar
    private lateinit var tvAllocatedRam: TextView
    private lateinit var tvHashes: TextView
    private lateinit var tvExecutionTime: TextView
    private lateinit var tvHashRate: TextView
    private lateinit var tvProofDigest: TextView
    private lateinit var tvErrorMessage: TextView

    private val serviceConnection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, binder: IBinder?) {
            val localBinder = binder as? PoStDaemonService.LocalBinder
            daemonService = localBinder?.getService()
            isBound = true
            observeDaemonState()
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            daemonService = null
            isBound = false
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        buildUiLayout()
        requestNotificationPermissionIfNeeded()
    }

    override fun onStart() {
        super.onStart()
        val intent = Intent(this, PoStDaemonService::class.java)
        bindService(intent, serviceConnection, Context.BIND_AUTO_CREATE)
    }

    override fun onStop() {
        super.onStop()
        observationJob?.cancel()
        observationJob = null
        if (isBound) {
            unbindService(serviceConnection)
            isBound = false
        }
    }

    private fun observeDaemonState() {
        observationJob?.cancel()
        observationJob = lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                daemonService?.stateFlow?.collect { state ->
                    updateUi(state)
                }
            }
        }
    }

    private fun updateUi(state: PoStState) {
        tvStatus.text = when (state.status) {
            PoStStatus.IDLE -> getString(R.string.status_idle)
            PoStStatus.ALLOCATING_MEMORY -> getString(R.string.status_allocating)
            PoStStatus.PROVING -> getString(R.string.status_proving)
            PoStStatus.PAUSED -> getString(R.string.status_paused)
            PoStStatus.CANCELLED -> getString(R.string.status_cancelled)
            PoStStatus.COMPLETED -> getString(R.string.status_completed)
            PoStStatus.FAILED -> getString(R.string.status_failed)
        }

        val statusColor = when (state.status) {
            PoStStatus.COMPLETED -> Color.parseColor("#2E7D32")
            PoStStatus.PROVING, PoStStatus.ALLOCATING_MEMORY -> Color.parseColor("#1565C0")
            PoStStatus.PAUSED, PoStStatus.CANCELLED -> Color.parseColor("#EF6C00")
            PoStStatus.FAILED -> Color.parseColor("#C62828")
            PoStStatus.IDLE -> Color.parseColor("#424242")
        }
        tvStatus.setTextColor(statusColor)

        btnStart.isEnabled = !state.isRunning
        btnCancel.isEnabled = state.isRunning
        etRam.isEnabled = !state.isRunning
        etIterations.isEnabled = !state.isRunning

        if (state.status == PoStStatus.PROVING || state.status == PoStStatus.ALLOCATING_MEMORY) {
            progressBar.visibility = View.VISIBLE
            progressBar.isIndeterminate = (state.status == PoStStatus.ALLOCATING_MEMORY)
        } else {
            progressBar.visibility = View.GONE
        }

        val ramMbDisplay = if (state.allocatedMemoryMb > 0) state.allocatedMemoryMb else (etRam.text.toString().toIntOrNull() ?: 16)
        val ramBytesDisplay = if (state.allocatedRamBytes > 0) state.allocatedRamBytes else (ramMbDisplay.toLong() * 1024 * 1024)
        tvAllocatedRam.text = String.format(Locale.US, "Allocated RAM: %d MB (%d Bytes)", ramMbDisplay, ramBytesDisplay)

        tvHashes.text = String.format(Locale.US, "Completed Hashes: %d / %d", state.completedHashes, state.targetHashes)
        tvExecutionTime.text = String.format(Locale.US, "Execution Duration: %d ms", state.elapsedTimeMs)
        tvHashRate.text = String.format(Locale.US, "Current Hash Rate: %.2f H/s", state.currentHashRate)

        if (!state.proofHashHex.isNull_orEmpty()) {
            tvProofDigest.text = state.proofHashHex
            tvProofDigest.visibility = View.VISIBLE
        } else {
            tvProofDigest.text = "No proof generated yet."
        }

        if (!state.errorMessage.isNull_orEmpty()) {
            tvErrorMessage.text = String.format("Error: %s", state.errorMessage)
            tvErrorMessage.visibility = View.VISIBLE
        } else {
            tvErrorMessage.visibility = View.GONE
        }
    }

    private fun CharSequence?.isNull_orEmpty(): Boolean = this == null || this.isEmpty()

    private fun requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 101)
            }
        }
    }

    private fun buildUiLayout() {
        val rootScrollView = ScrollView(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.MATCH_PARENT
            )
            isFillViewport = true
            setBackgroundColor(Color.parseColor("#F5F5F7"))
        }

        val mainContainer = LinearLayout(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            orientation = LinearLayout.VERTICAL
            val pad = dpToPx(16)
            setPadding(pad, pad, pad, pad)
        }

        // Header Card
        val headerCard = createCardView().apply {
            val contentLayout = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
                val pad = dpToPx(16)
                setPadding(pad, pad, pad, pad)

                addView(TextView(this@MainActivity).apply {
                    text = getString(R.string.app_name)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 22f)
                    setTypeface(null, Typeface.BOLD)
                    setTextColor(Color.parseColor("#1C1B1F"))
                })

                addView(TextView(this@MainActivity).apply {
                    text = "Bare-Metal PoST Infrastructure Node"
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                    setTextColor(Color.parseColor("#49454F"))
                })
            }
            addView(contentLayout)
        }
        mainContainer.addView(headerCard)

        // Configuration & Control Card
        val controlCard = createCardView().apply {
            val contentLayout = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
                val pad = dpToPx(16)
                setPadding(pad, pad, pad, pad)

                val statusRow = LinearLayout(this@MainActivity).apply {
                    orientation = LinearLayout.HORIZONTAL
                    gravity = Gravity.CENTER_VERTICAL
                }
                statusRow.addView(TextView(this@MainActivity).apply {
                    text = getString(R.string.label_status)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
                    setTypeface(null, Typeface.BOLD)
                })
                tvStatus = TextView(this@MainActivity).apply {
                    text = getString(R.string.status_idle)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
                    setTypeface(null, Typeface.BOLD)
                    val padH = dpToPx(8)
                    setPadding(padH, 0, 0, 0)
                }
                statusRow.addView(tvStatus)
                addView(statusRow)

                // RAM Input Label & EditText
                addView(TextView(this@MainActivity).apply {
                    text = getString(R.string.label_ram_alloc)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                    setPadding(0, dpToPx(12), 0, dpToPx(4))
                })
                etRam = EditText(this@MainActivity).apply {
                    setText("16")
                    inputType = InputType.TYPE_CLASS_NUMBER
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
                }
                addView(etRam)

                // Iterations Input Label & EditText
                addView(TextView(this@MainActivity).apply {
                    text = getString(R.string.label_iterations)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                    setPadding(0, dpToPx(12), 0, dpToPx(4))
                })
                etIterations = EditText(this@MainActivity).apply {
                    setText("1000")
                    inputType = InputType.TYPE_CLASS_NUMBER
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
                }
                addView(etIterations)

                // Buttons Layout
                val buttonLayout = LinearLayout(this@MainActivity).apply {
                    orientation = LinearLayout.HORIZONTAL
                    setPadding(0, dpToPx(16), 0, 0)
                }

                btnStart = Button(this@MainActivity).apply {
                    text = getString(R.string.btn_start)
                    layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
                    setOnClickListener {
                        val ram = etRam.text.toString().toIntOrNull() ?: 16
                        val iterations = etIterations.text.toString().toIntOrNull() ?: 1000

                        val intent = Intent(this@MainActivity, PoStDaemonService::class.java)
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            startForegroundService(intent)
                        } else {
                            startService(intent)
                        }
                        if (!isBound) {
                            bindService(intent, serviceConnection, Context.BIND_AUTO_CREATE)
                        }
                        daemonService?.startPoSt(ram, iterations)
                    }
                }

                btnCancel = Button(this@MainActivity).apply {
                    text = getString(R.string.btn_cancel)
                    isEnabled = false
                    layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f).apply {
                        setMargins(dpToPx(8), 0, 0, 0)
                    }
                    setOnClickListener {
                        daemonService?.cancelPoSt()
                    }
                }

                buttonLayout.addView(btnStart)
                buttonLayout.addView(btnCancel)
                addView(buttonLayout)
            }
            addView(contentLayout)
        }
        mainContainer.addView(controlCard)

        // Real-Time Metrics Card
        val metricsCard = createCardView().apply {
            val contentLayout = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
                val pad = dpToPx(16)
                setPadding(pad, pad, pad, pad)

                addView(TextView(this@MainActivity).apply {
                    text = "Real-Time Node Metrics"
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 18f)
                    setTypeface(null, Typeface.BOLD)
                    setPadding(0, 0, 0, dpToPx(8))
                })

                progressBar = ProgressBar(this@MainActivity, null, android.R.attr.progressBarStyleHorizontal).apply {
                    visibility = View.GONE
                    layoutParams = LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT
                    ).apply { setMargins(0, 0, 0, dpToPx(12)) }
                }
                addView(progressBar)

                tvAllocatedRam = TextView(this@MainActivity).apply {
                    text = "Allocated RAM: 0 MB (0 Bytes)"
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                }
                addView(tvAllocatedRam)

                tvHashes = TextView(this@MainActivity).apply {
                    text = "Completed Hashes: 0 / 0"
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                    setPadding(0, dpToPx(4), 0, 0)
                }
                addView(tvHashes)

                tvExecutionTime = TextView(this@MainActivity).apply {
                    text = "Execution Duration: 0 ms"
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                    setPadding(0, dpToPx(4), 0, 0)
                }
                addView(tvExecutionTime)

                tvHashRate = TextView(this@MainActivity).apply {
                    text = "Current Hash Rate: 0.00 H/s"
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                    setPadding(0, dpToPx(4), 0, 0)
                }
                addView(tvHashRate)
            }
            addView(contentLayout)
        }
        mainContainer.addView(metricsCard)

        // Proof Output Card
        val proofCard = createCardView().apply {
            val contentLayout = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.VERTICAL
                val pad = dpToPx(16)
                setPadding(pad, pad, pad, pad)

                addView(TextView(this@MainActivity).apply {
                    text = getString(R.string.label_proof_digest)
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 18f)
                    setTypeface(null, Typeface.BOLD)
                    setPadding(0, 0, 0, dpToPx(8))
                })

                tvProofDigest = TextView(this@MainActivity).apply {
                    text = "No proof generated yet."
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 13f)
                    setTypeface(Typeface.MONOSPACE)
                    setBackgroundColor(Color.parseColor("#E0E0E0"))
                    val p = dpToPx(8)
                    setPadding(p, p, p, p)
                    setTextIsSelectable(true)
                }
                addView(tvProofDigest)

                tvErrorMessage = TextView(this@MainActivity).apply {
                    visibility = View.GONE
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
                    setTextColor(Color.parseColor("#C62828"))
                    setTypeface(null, Typeface.BOLD)
                    setPadding(0, dpToPx(8), 0, 0)
                }
                addView(tvErrorMessage)
            }
            addView(contentLayout)
        }
        mainContainer.addView(proofCard)

        rootScrollView.addView(mainContainer)
        setContentView(rootScrollView)
    }

    private fun createCardView(): CardView {
        return CardView(this).apply {
            val params = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            params.setMargins(0, 0, 0, dpToPx(16))
            layoutParams = params
            radius = dpToPx(12).toFloat()
            cardElevation = dpToPx(4).toFloat()
            setCardBackgroundColor(Color.WHITE)
        }
    }

    private fun dpToPx(dp: Int): Int {
        return TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP,
            dp.toFloat(),
            resources.displayMetrics
        ).toInt()
    }
}
